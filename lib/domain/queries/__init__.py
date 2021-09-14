from ... import db
from .. import URI
from .signflow_pieces import signflow_pieces

def signflow_exists(signflow_uri: str):
    return db.exists(URI.graph.sign, URI.type.signflow, signflow_uri)

def piece_exists(piece_uri: str):
    return db.exists(URI.graph.sign, URI.type.piece, piece_uri)
