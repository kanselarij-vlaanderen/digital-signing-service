from . import __signflow_queries

def get_signflow_signers(signflow_uri: str):
    records = __signflow_queries.get_signers(signflow_uri)
    signers = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return signers
