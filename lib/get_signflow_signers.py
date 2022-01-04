from . import signflow

def get_signflow_signers(signflow_uri: str):
    records = signflow.get_signers(signflow_uri)
    signers = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return signers
