from . import signflow

def get_signflow_pieces(signflow_uri: str):
    records = signflow.get_pieces(signflow_uri)
    pieces = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return pieces
