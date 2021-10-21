from . import uri, GetPieces, Prepare
from .. import exceptions

def get_pieces(signflow_uri: str):
    records = GetPieces.execute(signflow_uri)
    if records is None:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    return records

prepare = Prepare.execute
