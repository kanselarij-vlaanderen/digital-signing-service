from string import Template
from helpers import query
from escape_helpers import sparql_escape_string, sparql_escape_uri
from . import exceptions, helpers, uri, validate
from ..queries import signflow_pieces

def get_signflow_pieces(signflow_uri: str):
    query_command = signflow_pieces.construct_signflow_pieces_query(signflow_uri)
    results = query(query_command)
    records = helpers.to_recs(results)

    if not records:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    has_piece = "piece_id" in records[0]
    if not has_piece:
        return []

    records = [{
        "id": r["piece_id"],
        "uri": r["piece"],
        "status": _get_status(r),
    } for r in records]

    return records

def _get_status(record):
    switcher = {
        "http://mu.semte.ch/vocabularies/ext/handteken/Markeringsactiviteit": "marked",
        "http://mu.semte.ch/vocabularies/ext/handteken/Voorbereidingsactiviteit": "prepared",
        "http://mu.semte.ch/vocabularies/ext/handteken/Handtekenactiviteit": "open",
    }
    status = switcher.get(record["activity_type"])
    return status
