import os
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from helpers import log

DIGITAL_SIGNING_AGENT_ALLOWED_GROUPS =   [ # Secretarie
    { "variables": [], "name": "public" },
    { "variables": [], "name": "authenticated" },
    { "variables": [], "name": "secretarie" },
    { "variables": [], "name": "sign-flow-read" },
    { "variables": [], "name": "sign-flow-write" },
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
    log(f"(agent query) execute query: \n" + the_query)
    sparqlQuery.setQuery(the_query)
    return sparqlQuery.query().convert()


def update(the_query):
    """Execute the given update SPARQL query on the triple store,
    if the given query is no update query, nothing happens."""
    sparqlUpdate.setQuery(the_query)
    if sparqlUpdate.isSparqlUpdateRequest():
        log("(agent update) execute query: \n" + the_query)
        sparqlUpdate.query()
