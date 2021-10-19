from . import uri, pieces, prepare as Prepare
from .. import exceptions

def get_signflow_pieces(signflow_uri: str):
    records = pieces.execute(signflow_uri)
    if records is None:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    return records

prepare = Prepare.execute
