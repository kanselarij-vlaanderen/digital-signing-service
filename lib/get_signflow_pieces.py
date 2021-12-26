from . import __signflow_queries

def get_signflow_pieces(signflow_uri: str):
    records = __signflow_queries.get_pieces(signflow_uri)
    pieces = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return pieces
