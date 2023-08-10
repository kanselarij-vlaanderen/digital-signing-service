from typing import Callable

from helpers import log, query

from ..config import APPLICATION_GRAPH
from ..queries.mandatee import construct_get_mandatee
from .exceptions import NoQueryResultsException


def get_mandatee(mandatee_uri, query_method: Callable = query):
    query_str = construct_get_mandatee(mandatee_uri)
    madatee_results = query_method(query_str)['results']['bindings']
    if not madatee_results:
        raise NoQueryResultsException("No mandatee with configured user account found by uri <{}>".format(mandatee_uri))
    mandatee = {k: v["value"] for k, v in madatee_results[0].items()}
    return mandatee
