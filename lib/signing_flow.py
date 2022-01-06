from ..queries.signing_flow import construct_by_mu_uuid
from .exceptions import NoQueryResultsException
from helpers import query
from . import query_result_helpers
from .. import queries

def get_signing_flow_by_uuid(uuid):
    query_str = construct_by_mu_uuid(uuid)
    signflow_results = query(query_str)['results']['bindings']
    if not signflow_results:
        raise NoQueryResultsException("No signflow found by uuid '{}'".format(uuid))
    signflow_uri = signflow_results[0]["signflow"]["value"]
    return signflow_uri

def get_signing_flow(signflow_uri: str):
    query_command = queries.signing_flow.construct(signflow_uri)
    return __get_signflow_record(query_command)

def get_signflow_by_signinghub_id(sh_package_id: str):
    query_command = queries.signing_flow.construct_by_signinghub_id(sh_package_id)
    return __get_signflow_record(query_command)

def __get_signflow_record(query_command: str):
    result = query(query_command)
    records = query_result_helpers.to_recs(result)
    record = query_result_helpers.ensure_1(records)

    record = {
        "id": record["signflow_id"],
        "uri": record["signflow"],
        "sh_package_id": record["sh_package_id"],
    }

    return record

def get_pieces(signflow_uri: str):
    query_command = queries.signing_flow_pieces.construct(signflow_uri)
    result = query(query_command)
    records = query_result_helpers.to_recs(result)
    query_result_helpers.ensure_1(records)

    records = [{
        "id": r["piece_id"],
        "uri": r["piece"],
        "sh_document_id": r["sh_document_id"],
    } for r in records]

    return records

def get_signers(signflow_uri: str):
    query_command = queries.signing_flow_signers.construct(signflow_uri)
    result = query(query_command)
    records = query_result_helpers.to_recs(result)

    records = [{
        "id": r["signer_id"],
        "uri": r["signer"],
        "signing_activity": r["signing_activity"],
        "start_date": r["start_date"],
        "end_date": r["end_date"],
    } for r in records]

    return records
