from helpers import query, log
from ..queries.mandatee import construct_get_mandatee, \
    construct_get_mandatee_by_email
from .exceptions import NoQueryResultsException

def get_mandatee(mandatee_uri):
    query_str = construct_get_mandatee(mandatee_uri)
    madatee_results = query(query_str)['results']['bindings']
    if not madatee_results:
        raise NoQueryResultsException("No mandatee found by uri <{}>".format(mandatee_uri))
    mandatee = {k: v["value"] for k, v in madatee_results[0].items()}
    return mandatee

def get_mandatee_by_email(mandatee_email):
    query_str = construct_get_mandatee_by_email(mandatee_email)
    madatee_results = query(query_str)['results']['bindings']
    if not madatee_results:
        raise NoQueryResultsException("No mandatee found by id '{}'".format(mandatee_email))
    if madatee_results.length > 1:
        log("Multiple mandatees found for e-mail address '{}'. Picking one.".format(mandatee_email))
    mandatee = {k: v["value"] for k, v in madatee_results[0].items()}
    return mandatee

def get_mandatee_email(mandatee_uri):
    mandatee = get_mandatee(mandatee_uri)
    if "email" not in mandatee:
        raise NoQueryResultsException("The mandatee by uri <{}> has no known email address".format(mandatee_uri))
    return mandatee["email"]
