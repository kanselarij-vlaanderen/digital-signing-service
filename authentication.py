import os
from functools import wraps

from flask import g, request
from helpers import error, generate_uuid, log, logger
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

SIGNINGHUB_API_CLIENT_ID = os.environ.get("SIGNINGHUB_CLIENT_ID")
SIGNINGHUB_API_CLIENT_SECRET = os.environ.get("SIGNINGHUB_CLIENT_SECRET") # API key
SIGNINGHUB_MACHINE_ACCOUNT_USERNAME = os.environ.get("SIGNINGHUB_MACHINE_ACCOUNT_USERNAME")
SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD = os.environ.get("SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD")

SIGNINGHUB_SESSION_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/signinghub-sessions/"

def ensure_signinghub_session(mu_session_uri):
    """For api interactions made through Kaleidos initiated by a user"""
    mu_session_query = construct_get_mu_session_query(mu_session_uri)
    mu_session_result = sudo_query(mu_session_query)['results']['bindings']
    if not mu_session_result:
        raise NoQueryResultsException("Didn't find a mu-session associated with an account with email-address and supported ovo-code")
    mu_session = mu_session_result[0]
    sh_session_query = construct_get_signinghub_session_query(mu_session_uri)
    sh_session_results = sudo_query(sh_session_query)['results']['bindings']
    if sh_session_results: # Restore SigningHub session
        log("Found a valid SigningHub session.")
        sh_session_result = sh_session_results[0]
        g.sh_session = SigningHubSession(SIGNINGHUB_API_URL)
        if CLIENT_CERT_AUTH_ENABLED:
            g.sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
        g.sh_session.access_token = sh_session_result["token"]["value"]
    else: # Open new SigningHub session
        log("No valid SigningHub session found. Opening a new one ...")
        sh_session = open_new_signinghub_machine_user_session(mu_session["ovoCode"]["value"], mu_session["email"]["value"])
        sh_session_uri = SIGNINGHUB_SESSION_BASE_URI + generate_uuid()
        sh_session_query = construct_insert_signinghub_session_query(sh_session, sh_session_uri)
        sudo_update(sh_session_query)
        sh_session_link_query = construct_attach_signinghub_session_to_mu_session_query(sh_session_uri, mu_session_uri)
        sudo_update(sh_session_link_query)
        g.sh_session = sh_session

def signinghub_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        mu_session_id = request.headers["MU-SESSION-ID"]
        try:
            ensure_signinghub_session(mu_session_id)
            return f(*args, **kwargs)
        except AuthenticationException as ex:
            logger.exception("Authentication Error")
            return error(ex.error_description, code="digital-signing.signinghub.{}".format(ex.error_id))
        except NoQueryResultsException as ex:
            logger.exception("No Query Results Error")
            return error(ex.args[0])
    return decorated_function

def open_new_signinghub_machine_user_session(ovo_code, scope=None):
    sh_session = SigningHubSession(SIGNINGHUB_API_URL)
    if CLIENT_CERT_AUTH_ENABLED:
        sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
    account_details = MACHINE_ACCOUNTS[ovo_code]
    sh_session.authenticate(account_details["API_CLIENT_ID"],
                            account_details["API_CLIENT_SECRET"],
                            "password", # grant type
                            account_details["USERNAME"],
                            account_details["PASSWORD"],
                            scope)
    return sh_session

def ensure_signinghub_machine_user_session(scope=None):
    """For interactions made by the service agent (initiated by cron job or similar)"""
    sh_session_query = construct_get_signinghub_machine_user_session_query(scope)
    sh_session_results = sudo_query(sh_session_query)['results']['bindings']
    if sh_session_results: # Restore SigningHub session
        log("Found a valid SigningHub session.")
        sh_session_result = sh_session_results[0]
        g.sh_session = SigningHubSession(SIGNINGHUB_API_URL)
        if CLIENT_CERT_AUTH_ENABLED:
            g.sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
        g.sh_session.access_token = sh_session_result["token"]["value"]
    else: # Open new SigningHub session
        log("No valid SigningHub session found. Opening a new one ...")
        ovo_code = sudo_query(construct_get_org_for_email(scope))['results']['bindings'][0]['ovoCode']['value']
        sh_session = open_new_signinghub_machine_user_session(ovo_code, scope)
        sh_session_uri = SIGNINGHUB_SESSION_BASE_URI + generate_uuid()
        sh_session_query = construct_insert_signinghub_session_query(sh_session, sh_session_uri, scope)
        sudo_update(sh_session_query)
        sh_session_sudo_query = construct_mark_signinghub_session_as_machine_users_query(sh_session_uri)
        sudo_update(sh_session_sudo_query)
        g.sh_session = sh_session
