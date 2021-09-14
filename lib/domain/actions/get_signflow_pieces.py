from ... import db, exceptions
from ...db import uri, string, file_rel
from .. import URI, queries

def get_signflow_pieces(signflow_uri: str):
    exists = queries.signflow_exists(signflow_uri)
    if not exists:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    records = queries.signflow_pieces(signflow_uri)
    return records
