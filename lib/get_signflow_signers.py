from . import validate, __signflow_queries

def get_signflow_signers(signflow_uri: str):
    validate.ensure_signflow_exists(signflow_uri)

    records = __signflow_queries.get_signers(signflow_uri)
    signers = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return signers
