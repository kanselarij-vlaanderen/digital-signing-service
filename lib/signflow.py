from ..queries.signflow import construct_by_mu_uuid
from .exceptions import NoQueryResultsException
from helpers import query

def get_signflow_by_uuid(uuid):
    query_str = construct_by_mu_uuid(uuid)
    signflow_results = query(query_str)['results']['bindings']
    if not signflow_results:
        raise NoQueryResultsException("No signflow found by uuid '{}'".format(uuid))
    signflow_uri = signflow_results[0]["signflow"]["value"]
    return signflow_uri
