import os
from functools import wraps

from flask import g, request
from helpers import error, generate_uuid, logger
from signinghub_api_client.client import SigningHubSession
from signinghub_api_client.exceptions import AuthenticationException

from .authentication_config import MACHINE_ACCOUNTS
from .config import KALEIDOS_RESOURCE_BASE_URI
from .lib.exceptions import NoQueryResultsException
from .queries.session import (
    construct_attach_signinghub_session_to_mu_session_query,
    construct_get_mu_session_query, construct_get_org_for_email,
    construct_get_signinghub_machine_user_session_query,
    construct_get_signinghub_session_query,
    construct_insert_signinghub_session_query,
    construct_mark_signinghub_session_as_machine_users_query)
from .sudo_query import query as sudo_query
from .sudo_query import update as sudo_update

SIGNINGHUB_API_URL = os.environ.get("SIGNINGHUB_API_URL")
CERT_FILE_PATH = os.environ.get("CERT_FILE_PATH")
KEY_FILE_PATH = os.environ.get("KEY_FILE_PATH")
CLIENT_CERT_AUTH_ENABLED = CERT_FILE_PATH and KEY_FILE_PATH

SIGNINGHUB_SESSION_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/signinghub-sessions/"

def get_or_create_signinghub_session(mu_session_uri):
    mu_session_query = construct_get_mu_session_query(mu_session_uri)
    mu_session_result = sudo_query(mu_session_query)['results']['bindings']
    if not mu_session_result:
        raise NoQueryResultsException("Didn't find a mu-session associated with an account with email-address and supported ovo-code")
    mu_session = mu_session_result[0]
    sh_session_query = construct_get_signinghub_session_query(mu_session_uri)
    sh_session_results = sudo_query(sh_session_query)['results']['bindings']
    sh_session = None
    if sh_session_results: # Restore SigningHub session
        logger.debug("Found a valid SigningHub session.")
        sh_session_result = sh_session_results[0]
        sh_session = SigningHubSession(SIGNINGHUB_API_URL)
        if CLIENT_CERT_AUTH_ENABLED:
            sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
        sh_session.access_token = sh_session_result["token"]["value"]
    else: # Open new SigningHub session
        logger.debug("No valid SigningHub session found. Opening a new one ...")
        sh_session = open_new_signinghub_machine_user_session(mu_session["ovoCode"]["value"], mu_session["email"]["value"])
        sh_session_uri = SIGNINGHUB_SESSION_BASE_URI + generate_uuid()
        sh_session_query = construct_insert_signinghub_session_query(sh_session, sh_session_uri)
        sudo_update(sh_session_query)
        sh_session_link_query = construct_attach_signinghub_session_to_mu_session_query(sh_session_uri, mu_session_uri)
        sudo_update(sh_session_link_query)
    return sh_session

def ensure_signinghub_session(mu_session_uri):
    """For api interactions made through Kaleidos initiated by a user"""
    sh_session = get_or_create_signinghub_session(mu_session_uri)
    g.sh_session = sh_session

def open_new_signinghub_machine_user_session(ovo_code, scope=None):
    sh_session = SigningHubSession(SIGNINGHUB_API_URL)
    if CLIENT_CERT_AUTH_ENABLED:
        sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
    account_details = MACHINE_ACCOUNTS[ovo_code]
    sh_session.authenticate(account_details["API_CLIENT_ID"],
                            account_details["API_CLIENT_SECRET"],
                            grant_type="client_credentials",
                            scope=scope)
    return sh_session


def set_signinghub_machine_user_session(session):
    logger.debug("Found a valid SigningHub session.")
    g.sh_session = SigningHubSession(SIGNINGHUB_API_URL)
    if CLIENT_CERT_AUTH_ENABLED:
        g.sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
    g.sh_session.access_token = session["token"]["value"]


def create_signinghub_machine_user_session(scope, ovo_code):
    logger.debug("No valid SigningHub session found. Opening a new one ...")
    sh_session = open_new_signinghub_machine_user_session(ovo_code, scope)
    sh_session_uri = SIGNINGHUB_SESSION_BASE_URI + generate_uuid()
    sh_session_query = construct_insert_signinghub_session_query(sh_session, sh_session_uri, scope)
    sudo_update(sh_session_query)
    sh_session_sudo_query = construct_mark_signinghub_session_as_machine_users_query(sh_session_uri)
    sudo_update(sh_session_sudo_query)
    g.sh_session = sh_session
