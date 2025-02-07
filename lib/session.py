from .exceptions import NoQueryResultsException
from ..sudo_query import query as sudo_query
from ..queries.session import construct_get_mu_session_query

def get_mu_session(mu_session_uri):
    mu_session_query = construct_get_mu_session_query(mu_session_uri)
    mu_session_result = sudo_query(mu_session_query)['results']['bindings']
    if not mu_session_result:
        raise NoQueryResultsException("Didn't find a mu-session associated with an account with email-address and supported ovo-code")
    mu_session = mu_session_result[0]
    return mu_session