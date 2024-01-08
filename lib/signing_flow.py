# from ..queries.signing_flow import construct_by_mu_uuid
from typing import Callable

from helpers import query

from .. import queries
from ..config import APPLICATION_GRAPH
from ..queries.signing_flow import (construct_get_ongoing_signing_flows,
                                    construct_get_signing_flow_by_uri,
                                    construct_get_signing_flow_creator)
from . import query_result_helpers
from .exceptions import NoQueryResultsException


def get_signing_flow(signflow_uri: str, query_method: Callable = query):
    query_string = construct_get_signing_flow_by_uri(signflow_uri)
    result = query_method(query_string)
    records = query_result_helpers.to_recs(result)
    record = query_result_helpers.ensure_1(records)
    return record

def get_pieces(signflow_uri: str, query_method: Callable = query):
    query_command = queries.signing_flow_pieces.construct(signflow_uri)
    result = query_method(query_command)
    records = query_result_helpers.to_recs(result)
    query_result_helpers.ensure_1(records)

    records = [{
        "id": r["piece_id"],
        "uri": r["piece"],
        "sh_document_id": r["sh_document_id"],
    } for r in records]

    return records

def get_signers(signflow_uri: str, query_method: Callable = query):
    query_command = queries.signing_flow_signers.construct(signflow_uri)
    result = query_method(query_command)
    records = query_result_helpers.to_recs(result)

    records = [{
        "id": r["signer_id"],
        "uri": r["signer"],
        "signing_activity": r["signing_activity"],
        "start_date": r["start_date"],
        "end_date": r["end_date"],
        "email": r["email"],
    } for r in records]

    return records

def get_approvers(signflow_uri: str, query_method: Callable = query):
    query_command = queries.signing_flow_approvers.construct(signflow_uri)
    result = query_method(query_command)
    records = query_result_helpers.to_recs(result)

    records = [{
        "email": r["approver"].replace("mailto:", ""),
        "approval_activity": r["approval_activity"],
        "start_date": r["start_date"],
        "end_date": r["end_date"],
    } for r in records]

    return records

def get_notified(signflow_uri: str, query_method: Callable = query):
    query_command = queries.signing_flow.construct_get_signing_flow_notifiers(signflow_uri)
    result = query_method(query_command)
    records = query_result_helpers.to_recs(result)

    records = [{
        "email": r["notified"].replace("mailto:", ""),
    } for r in records]

    return records

def get_creator(signflow_uri: str, query_method: Callable = query):
    query_string = construct_get_signing_flow_creator(signflow_uri)
    result = query_method(query_string)
    records = query_result_helpers.to_recs(result)
    record = query_result_helpers.ensure_1(records)
    return record

def get_ongoing_signing_flows(query_method: Callable = query):
    query_string = construct_get_ongoing_signing_flows()
    result = query_method(query_string)
    records = query_result_helpers.to_recs(result)
    return records
