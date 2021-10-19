from string import Template
from helpers import query
from escape_helpers import sparql_escape_string, sparql_escape_uri
from .. import exceptions, sparql
from . import uri

def execute(signflow_uri: str):
    template = Template(sparql.relative_file("pieces.sparql"))
    query_command = template.safe_substitute({
        "graph": sparql_escape_uri(uri.graph.sign),
        "signflow": sparql_escape_uri(signflow_uri)
    })
    
    results = query(query_command)
    records = sparql.to_recs(results)
    if len(records) == 0:
        return None

    has_piece = "id" in records[0]
    if not has_piece:
        return []

    records = [{
        "id": r["id"],
        "uri": r["uri"],
        "status": _get_status(r),
    } for r in records]

    return records

def _get_status(record):
    if "preparation_activity" in record:
        return "prepared"
    elif "marking_activity" in record:
        return "marked"
    else:
        raise Exception("status-unknown")
