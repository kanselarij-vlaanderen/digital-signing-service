from . import signing_flow

def get_signflow_signers(signflow_uri: str):
    records = signing_flow.get_signers(signflow_uri)
    signers = [{
        "id": r["id"],
        "uri": r["uri"],
    } for r in records]

    return signers
