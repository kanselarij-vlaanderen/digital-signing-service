from ... import db, exceptions
from ...db import uri, string, file_rel
from .. import URI, queries


def signflow_pieces(signflow_uri: str):
    results = db.query(file_rel("signflow_pieces.sparql"), {
        "graph": uri(URI.graph.sign),
        "signflow": uri(signflow_uri)
    })

    if "id" not in results[0]:
        return []

    records = [{
        "id": r["id"],
        "uri": r["uri"],
        "status": _get_status(r),
    } for r in results]

    return records

def _get_status(record):
    if "preparation_activity" in record:
        return "prepared"
    elif "marking_activity" in record:
        return "marked"
    else:
        raise Exception("status-unknown")
