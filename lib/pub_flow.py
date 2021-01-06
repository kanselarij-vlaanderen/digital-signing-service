from helpers import query
from ..queries.pub_flow import construct_get_subcase_from_pub_flow_id
from .exceptions import NoQueryResultsException

def get_subcase_from_pub_flow_id(pub_flow_id):
    sc_query = construct_get_subcase_from_pub_flow_id(pub_flow_id)
    sc_results = query(sc_query)['results']['bindings']
    if not sc_results:
        raise NoQueryResultsException("No signing subcase found from publication-flow by id '{}'".format(pub_flow_id))
    sc = {k: v["value"] for k, v in sc_results[0].items()}
    return sc

