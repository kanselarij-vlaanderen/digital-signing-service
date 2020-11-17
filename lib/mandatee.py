from helpers import query
from ..queries.mandatee import construct_get_mandatee
from .exceptions import NoQueryResultsException

def get_mandatee(mandatee_uri):
    query_str = construct_get_mandatee(mandatee_uri)
    madatee_results = query(query_str)['results']['bindings']
    if not madatee_results:
        raise NoQueryResultsException("No mandatee found by uri <{}>".format(mandatee_uri))
    mandatee = madatee_results[0]
    return mandatee

def get_mandatee_email(mandatee_uri):
    mandatee = get_mandatee(mandatee_uri)
    if "email" not in mandatee:
        raise NoQueryResultsException("The mandatee by uri <{}> has no known email address".format(mandatee_uri))
    return mandatee["email"]
