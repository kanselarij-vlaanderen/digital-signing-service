from . import signing_flow

def get_signflow_pieces(signflow_uri: str):
    records = signing_flow.get_pieces(signflow_uri)
    pieces = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return pieces
