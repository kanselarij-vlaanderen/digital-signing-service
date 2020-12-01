import os
from functools import wraps
from pytz import timezone
from flask import g, request
from signinghub_api_client.client import SigningHubSession
from signinghub_api_client.exceptions import AuthenticationException
from helpers import log, error
from .queries.session import construct_get_mu_session_query, \
    construct_get_signinghub_session_query, \
    construct_insert_signinghub_session_query, \
    construct_get_signinghub_machine_user_session_query, \
    construct_insert_signinghub_machine_user_session_query
from .sudo_query import query as sudo_query, update as sudo_update
from .lib.exceptions import NoQueryResultsException

TIMEZONE = timezone('Europe/Brussels')

SIGNINGHUB_API_URL = os.environ.get("SIGNINGHUB_API_URL")
CERT_FILE_PATH = os.environ.get("CERT_FILE_PATH")
KEY_FILE_PATH = os.environ.get("KEY_FILE_PATH")

SIGNINGHUB_SSO_METHOD = "test" # TODO

SIGNINGHUB_API_CLIENT_ID = os.environ.get("SIGNINGHUB_CLIENT_ID")
SIGNINGHUB_API_CLIENT_SECRET = os.environ.get("SIGNINGHUB_CLIENT_SECRET") # API key
SIGNINGHUB_MACHINE_ACCOUNT_USERNAME = os.environ.get("SIGNINGHUB_MACHINE_ACCOUNT_USERNAME")
SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD = os.environ.get("SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD")

def open_new_signinghub_session(oauth_token, mu_session_uri):
    sh_session = SigningHubSession(SIGNINGHUB_API_URL)
    sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
    sh_session.authenticate_sso(oauth_token, SIGNINGHUB_SSO_METHOD)
    sh_session_params = {
        "creation_time": sh_session.last_successful_auth_time,
        "expiry_time": sh_session.last_successful_auth_time + sh_session.access_token_expiry_time,
        "token": sh_session.access_token
    }
    sh_session_query = construct_insert_signinghub_session_query(sh_session_params, mu_session_uri)
    sudo_update(sh_session_query)
    return sh_session

def ensure_signinghub_session(mu_session_uri):
    mu_session_query = construct_get_mu_session_query(mu_session_uri)
    mu_session_result = sudo_query(mu_session_query)['results']['bindings']
    if not mu_session_result:
        raise NoQueryResultsException("Didn't find a mu-session with an Oauth token.")
    mu_session = mu_session_result[0]
    sh_session_query = construct_get_signinghub_session_query(mu_session_uri)
    sh_session_results = sudo_query(sh_session_query)['results']['bindings']
    if sh_session_results: # Restore SigningHub session
        log("Found a valid SigningHub session.")
        sh_session_result = sh_session_results[0]
        g.sh_session = SigningHubSession(SIGNINGHUB_API_URL)
        g.sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
        g.sh_session.access_token = sh_session_result["token"]
    else: # Open new SigningHub session
        log("No valid SigningHub session found. Opening a new one ...")
        g.sh_session = open_new_signinghub_session(mu_session["oauthToken"], mu_session_uri)

def signinghub_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        mu_session_id = request.headers["MU-SESSION-ID"]
        try:
            ensure_signinghub_session(mu_session_id)
            return f(*args, **kwargs)
        except AuthenticationException as ex:
            return error(ex.error_description, code="digital-signing.signinghub.{}".format(ex.id))
        except NoQueryResultsException as ex:
            return error(ex.args[0])
    return decorated_function

def open_new_signinghub_machine_user_session():
    sh_session = SigningHubSession(SIGNINGHUB_API_URL)
    sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
    sh_session.authenticate(SIGNINGHUB_API_CLIENT_ID,
                            SIGNINGHUB_API_CLIENT_SECRET,
                            "password", # grant type
                            SIGNINGHUB_MACHINE_ACCOUNT_USERNAME,
                            SIGNINGHUB_MACHINE_ACCOUNT_PASSWORD)
    sh_session_params = {
        "creation_time": sh_session.last_successful_auth_time,
        "expiry_time": sh_session.last_successful_auth_time + sh_session.access_token_expiry_time,
        "token": sh_session.access_token
    }
    sh_session_query = construct_insert_signinghub_machine_user_session_query(sh_session_params)
    sudo_update(sh_session_query)
    return sh_session

def ensure_signinghub_machine_user_session():
    sh_session_query = construct_get_signinghub_machine_user_session_query()
    sh_session_results = sudo_query(sh_session_query)['results']['bindings']
    if sh_session_results: # Restore SigningHub session
        log("Found a valid SigningHub session.")
        sh_session_result = sh_session_results[0]
        g.sh_session = SigningHubSession(SIGNINGHUB_API_URL)
        g.sh_session.cert = (CERT_FILE_PATH, KEY_FILE_PATH) # For authenticating against VO-network
        g.sh_session.access_token = sh_session_result["token"]
    else: # Open new SigningHub session
        log("No valid SigningHub session found. Opening a new one ...")
        g.sh_session = open_new_signinghub_machine_user_session()

def signinghub_machine_session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            ensure_signinghub_machine_user_session()
            return f(*args, **kwargs)
        except AuthenticationException as ex:
            return error(ex.error_description, code="digital-signing.signinghub.{}".format(ex.id))
        except NoQueryResultsException as ex:
            return error(ex.args[0])
    return decorated_function
