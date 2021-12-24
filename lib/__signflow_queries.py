from helpers import query
from . import helpers
from .. import queries

def get_signflow(signflow_uri: str):
    query_command = queries.signflow.construct(signflow_uri)
    return __get_signflow_record(query_command)

def get_signflow_by_signinghub_id(sh_package_id: str):
    query_command = queries.signflow.construct_by_signinghub_id(sh_package_id)
    return __get_signflow_record(query_command)

def __get_signflow_record(query_command: str):
    result = query(query_command)
    records = helpers.to_recs(result)
    record = helpers.ensure_1(records)

    record = {
        "id": record["signflow_id"],
        "uri": record["signflow"],
        "sh_package_id": record["sh_package_id"],
    }

    return record

def get_pieces(signflow_uri: str):
    query_command = queries.signflow_pieces.construct(signflow_uri)
    result = query(query_command)
    records = helpers.to_recs(result)
    helpers.ensure_1(records)

    records = [{
        "id": r["piece_id"],
        "uri": r["piece"],
        "sh_document_id": r["sh_document_id"],
    } for r in records]

    return records

def get_signers(signflow_uri: str):
    query_command = queries.signflow_signers.construct(signflow_uri)
    result = query(query_command)
    records = helpers.to_recs(result)

    records = [{
        "id": r["signer_id"],
        "uri": r["signer"],
        "signing_activity": r["signing_activity"],
        "start_date": r["start_date"],
        "end_date": r["end_date"],
    } for r in records]

    return records
