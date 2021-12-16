from string import Template
from helpers import log, logger, generate_uuid, query, update
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime
from . import exceptions, helpers, uri, validate, __signflow_queries

def get_signflow_signers(signflow_uri: str):
    validate.ensure_signflow_exists(signflow_uri)

    records = __signflow_queries.get_signers(signflow_uri)
    signers = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return signers
