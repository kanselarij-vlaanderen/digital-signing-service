from string import Template
from . import exceptions, helpers, uri, validate, get_pieces

def execute(signflow_uri, piece_uri):
    validate.ensure_signflow_exists(signflow_uri)
    validate.ensure_piece_exists(piece_uri)

    pieces = get_pieces.execute(signflow_uri)
    piece = helpers.ensure_1(pieces)

    if piece["uri"] != piece_uri:
        raise exceptions.InvalidArgumentException(
            f"Piece {piece_uri} is not associated to signflow {signflow_uri}.")
    if piece["status"] not in ["prepared", "to-sign"]:
        raise exceptions.InvalidStateException(
            f"Piece {piece_uri} is not prepared to signflow {signflow_uri} yet.")
