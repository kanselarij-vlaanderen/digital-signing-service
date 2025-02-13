import json
import os

from helpers import logger, LOG_SPARQL_QUERIES, LOG_SPARQL_UPDATES
from SPARQLWrapper import JSON, SPARQLWrapper

DIGITAL_SIGNING_AGENT_ALLOWED_GROUPS =   [ # Secretarie
    { "variables": [], "name": "public" },
    { "variables": [], "name": "authenticated" },
    { "variables": [], "name": "kanselarij-read" },
    { "variables": [], "name": "kanselarij-write" },
    { "variables": [], "name": "sign-flow-read" },
    { "variables": [], "name": "sign-flow-write" },
    { "variables": [], "name": "parliament-flow-read" },
    { "variables": [], "name": "parliament-flow-write" },
    { "variables": [], "name": "clean" }
]

sparqlQuery = SPARQLWrapper(os.environ.get('MU_SPARQL_ENDPOINT'), returnFormat=JSON)
sparqlQuery.addCustomHttpHeader('MU-AUTH-ALLOWED-GROUPS', json.dumps(DIGITAL_SIGNING_AGENT_ALLOWED_GROUPS))
sparqlUpdate = SPARQLWrapper(os.environ.get('MU_SPARQL_UPDATEPOINT'), returnFormat=JSON)
sparqlUpdate.method = 'POST'
sparqlUpdate.addCustomHttpHeader('MU-AUTH-ALLOWED-GROUPS', json.dumps(DIGITAL_SIGNING_AGENT_ALLOWED_GROUPS))


def query(the_query):
    """Execute the given SPARQL query (select/ask/construct)on the triple store and returns the results
    in the given returnFormat (JSON by default)."""
    if LOG_SPARQL_QUERIES:
        logger.info("(AGENT) Execute query: \n" + the_query)
    sparqlQuery.setQuery(the_query)
    try:
        return sparqlQuery.query().convert()
    except Exception as e:
        logger.error("(AGENT) The following query caused an exception to be thrown: \n" + the_query)
        raise e


def update(the_query):
    """Execute the given update SPARQL query on the triple store,
    if the given query is no update query, nothing happens."""
    sparqlUpdate.setQuery(the_query)
    if sparqlUpdate.isSparqlUpdateRequest():
        if LOG_SPARQL_UPDATES:
            logger.info("(AGENT) Execute update: \n" + the_query)
        try:
            sparqlUpdate.query()
        except Exception as e:
            logger.error("(AGENT) The following query caused an exception to be thrown: \n" + the_query)
            raise e
