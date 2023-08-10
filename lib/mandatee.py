from helpers import query, log
from typing import Callable
from ..queries.mandatee import construct_get_mandatee, \
    construct_get_mandatee_by_id
from .exceptions import NoQueryResultsException
from ..config import APPLICATION_GRAPH

def get_mandatee(mandatee_uri, query_method: Callable = query):
    query_str = construct_get_mandatee(mandatee_uri)
    madatee_results = query_method(query_str)['results']['bindings']
    if not madatee_results:
        raise NoQueryResultsException("No mandatee with configured user account found by uri <{}>".format(mandatee_uri))
    mandatee = {k: v["value"] for k, v in madatee_results[0].items()}
    return mandatee
