from datetime import datetime
from pytz import timezone
from flask import g
from helpers import query, update, generate_uuid, log
from ..sudo_query import query as sudo_query, update as sudo_update
from ..queries.document import construct_get_document_for_file, \
    construct_attach_document_to_previous_version
from ..queries.activity import \
    construct_get_signing_prep_from_sh_package_id, \
    construct_end_prep_start_signing, \
    construct_update_signing_activity, \
    construct_get_wrap_up_activity
from .mandatee import get_mandatee, get_mandatee_email, get_mandatee_by_email
from .document import download_sh_doc_to_kaleidos_doc
from .exceptions import NoQueryResultsException

TIMEZONE = timezone('Europe/Brussels')

SIGNING_PREP_ACT_BASE_URI = "http://example.com/activities/"

SIGNING_ACT_BASE_URI = "http://example.com/activities/"

SIGNING_ACT_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"
SIGNED_DOCS_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"

def update_activities_signing_started(signing_prep_uri):
    time = datetime.now(TIMEZONE)
    update_status_query = construct_end_prep_start_signing(signing_prep_uri,
                                                           time,
                                                           graph=SIGNING_ACT_GRAPH)
    sudo_update(update_status_query)

def update_signing_status(sh_package_id):
    workflow_details = g.sh_session.get_workflow_details(sh_package_id)
    for user in workflow_details["users"]:
        mandatee_uri = get_mandatee_by_email(user["user_email"])
        if user["process_status"] == "SIGNED": # "UN_PROCESSED", "IN_PROGRESS", "SIGNED", "REVIEWED", "DECLINED", "EDITED" or "INVALID"
            end_time = datetime.fromisoformat(user["processed_on"])
            for doc in workflow_details["documents"]: # Currently only one doc per package
                query_string = construct_update_signing_activity(sh_package_id,
                                                                 doc["document_id"],
                                                                 mandatee_uri,
                                                                 end_time,
                                                                 graph=SIGNING_ACT_GRAPH)
                sudo_update(query_string)
        else:
            log("User {} didn't perform a sign-action, but rather '{}'. \
                No update to the signing status performed.".format(user["user_email"], user["process_status"]))

def wrap_up_signing_flow(sh_package_id):
    workflow_details = g.sh_session.get_workflow_details(sh_package_id)
    workflow_status = workflow_details["workflow"]["workflow_status"]
    if workflow_status == "COMPLETED": # "DRAFT", "IN_PRGORESS" and "COMPLETED".
        wrap_up_act_qs = construct_get_wrap_up_activity(sh_package_id, SIGNING_ACT_GRAPH)
        wrap_up_results = sudo_query(wrap_up_act_qs)
        if not wrap_up_results:
            signing_prep_act_qs = construct_get_signing_prep_from_sh_package_id(sh_package_id, SIGNING_ACT_GRAPH)
            signing_prep_act = sudo_query(signing_prep_act_qs)['results']['bindings'][0] # Only 1 doc per activity normally
            new_doc = download_sh_doc_to_kaleidos_doc(sh_package_id, signing_prep_act["sh_document_id"]["value"])
            prev_doc_qs = construct_get_document_for_file(signing_prep_act["used_file"]["value"], SIGNED_DOCS_GRAPH)
            prev_doc = sudo_query(prev_doc_qs)['results']['bindings'][0]
            attach_qs = construct_attach_document_to_previous_version(new_doc["uri"], prev_doc["uri"]["value"], SIGNED_DOCS_GRAPH)
            sudo_update(attach_qs)
        else:
            log("Attempt to wrap up signing-flow was aborted because a wrap-up activity already exists (package-id {})".format(sh_package_id))
    else:
        log("Signing-flow status '{}' not eligible for wrapping up (package-id {})".format(workflow_status, sh_package_id))
                # end_time = datetime.fromisoformat(user["processed_on"])

