from datetime import datetime

from flask import g
from helpers import generate_uuid, logger
from signinghub_api_client.exceptions import SigningHubException

from utils import pythonize_iso_timestamp

from ..agent_query import query as agent_query
from ..agent_query import update as agent_update
from ..sudo_query import query as sudo_query
from ..authentication import (
    set_signinghub_machine_user_session,
    create_signinghub_machine_user_session)
from ..config import KALEIDOS_RESOURCE_BASE_URI
from ..queries.document import construct_attach_document_to_unsigned_version
from ..queries.signing_flow import construct_insert_cancellation_activity
from ..queries.signing_flow_approvers import (
    construct_insert_approval_activity,
    construct_insert_approval_refusal_activity,
    construct_update_approval_activity_end_date,
    construct_update_approval_activity_start_date)
from ..queries.signing_flow_signers import (
    construct_insert_signing_refusal_activity,
    construct_update_signing_activity_end_date,
    construct_update_signing_activity_start_date)
from ..queries.wrap_up_activity import construct_insert_wrap_up_activity
from ..queries.session import (
    construct_get_signinghub_machine_user_session_query,
    construct_get_org_for_email)
from .document import download_sh_doc_to_kaleidos_doc
from .signing_flow import (get_approvers, get_creator, get_pieces, get_signers,
                           get_signing_flow)

WRAP_UP_ACTIVITY_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/afrondingsactiviteit/"


def update_signing_flow(signflow_uri: str):
    signing_flow = get_signing_flow(signflow_uri, agent_query)
    signing_flow["uri"] = signflow_uri
    creator = get_creator(signflow_uri, agent_query)
    """
    There are multiple paths here

    - There are 1 or multiple existing, active SH sessions
    - Any of the sessions could work for checking the signing flow
    - None could work, in which case we need to get the user's OVO codes and mint a new session
    - There could be multiple OVO codes so we need to perform the operation with each session and see if it works

    Ideally, the Signing Flow stores the OVO code alongside the creator so we don't need to do all this, but currently
    existing flows will not have the OVO code so no matter how we slice it, we need to implement this retry mechanism
    Maybe down the line we can start storing OVO codes attached to signing flows, and then later on when all active
    signing flows have an OVO code we can remove the retry mechanism.
    """

    ovo_codes = sudo_query(
        construct_get_org_for_email(creator["email"])
    )["results"]["bindings"]
    sessions = sudo_query(
        construct_get_signinghub_machine_user_session_query(creator["email"])
    )["results"]["bindings"]

    last_exception = Exception() # A bit of a hack so we have an actual exception to throw

    if sessions:
        for session in sessions:
            try:
                set_signinghub_machine_user_session(session)
                return _update_signing_flow(signing_flow)
            except Exception as e:
                logger.debug("Tried to pull in signing flow updates with existing session but failed, retrying with other session...")
                last_exception = e
    # Either no sessions existed, or no existing ones worked, let's try making new sessions
    for ovo_code in ovo_codes:
        try:
            create_signinghub_machine_user_session(creator["email"], ovo_code["ovoCode"]["value"])
            return _update_signing_flow(signing_flow)
        except Exception as e:
            logger.debug("Tried to pull in signing flow updates with a new session but failed, retrying with other credentials if possible...")
            last_exception = e
    logger.warn("Could not pull in signing flow updates with existing nor new sessions...")
    raise last_exception


def _update_signing_flow(signing_flow):
    sh_package_id = signing_flow["sh_package_id"]
    signflow_uri = signing_flow["uri"]

    new_signing_flow_status = None
    try:
        sh_workflow_details = g.sh_session.get_workflow_details(sh_package_id)
        logger.debug(f'Signing flow {signflow_uri}, workflow status {sh_workflow_details["workflow"]["workflow_status"]}')
        if sh_workflow_details["workflow"]["workflow_status"] == "DRAFT":
            # Flow has not been shared yet by user, we can extract no information from it at this point
            pass
        if sh_workflow_details["workflow"]["workflow_status"] == "SHARED":
            approvers_changed = sync_approvers_status(signflow_uri, sh_workflow_details)
            signers_changed = sync_signers_status(signflow_uri, sh_workflow_details)
            new_signing_flow_status = "SHARED" if approvers_changed or signers_changed else None

        elif sh_workflow_details["workflow"]["workflow_status"] == "DECLINED":
            approvers_changed = sync_approvers_status(signflow_uri, sh_workflow_details)
            signers_changed = sync_signers_status(signflow_uri, sh_workflow_details)
            new_signing_flow_status = "DECLINED" if approvers_changed or signers_changed else None

        elif sh_workflow_details["workflow"]["workflow_status"] == "COMPLETED":
            sync_approvers_status(signflow_uri, sh_workflow_details)
            sync_signers_status(signflow_uri, sh_workflow_details)
            # TODO: check if everyone signed/approved/reviewed/... (didnt reject)
            doc = download_sh_doc_to_kaleidos_doc(sh_workflow_details["package_id"],
                                            signing_flow["sh_document_id"],
                                            "getekend document" # temporary name. Gets overwritten when attaching to source doc
                                            )

            attach_doc_qs = construct_attach_document_to_unsigned_version(doc["uri"],
                                                                        get_pieces(signflow_uri, agent_query)[0]["uri"])
            agent_update(attach_doc_qs)
            wrap_up_uuid = generate_uuid()
            wrap_up_uri = WRAP_UP_ACTIVITY_BASE_URI + wrap_up_uuid
            wrap_up_qs = construct_insert_wrap_up_activity(wrap_up_uri,
                                                        wrap_up_uuid,
                                                        datetime.now(), # TODO: parse the one from sign info instead
                                                        signflow_uri,
                                                        doc["uri"])
            agent_update(wrap_up_qs)
            new_signing_flow_status = "COMPLETED"
    except SigningHubException as e:
        if e.response.status_code == 404:
            logger.debug("Fetching workflow details resulted in a 404 response, marking flow as cancelled...")
            query_string = construct_insert_cancellation_activity(signflow_uri)
            agent_update(query_string)
            new_signing_flow_status = "CANCELLED"
        else:
            raise e

    return new_signing_flow_status


# Updates the approval activities in the DB based on the
# status of approvers we receive from SH
# Returns a boolean that denotes whether an activity has been updated in the DB
def sync_approvers_status(sig_flow, sh_workflow_details):
    sh_workflow_users = sh_workflow_details["users"]
    kaleidos_approvers = get_approvers(sig_flow, agent_query)
    approvers_changed = False

    logger.debug(f"Syncing approvers status ...")
    for sh_workflow_user in sh_workflow_users:
        if sh_workflow_user["role"] != "REVIEWER":
            continue
        proc_stat = sh_workflow_user["process_status"]
        logger.debug(f"Approver {sh_workflow_user['user_email']} has process status {proc_stat}.")
        if proc_stat == "UN_PROCESSED":
            continue
        kaleidos_approver = next(filter(lambda s: s["email"] == sh_workflow_user["user_email"], kaleidos_approvers), None)
        if kaleidos_approver:
            if not kaleidos_approver["end_date"]:
                if proc_stat == "IN_PROGRESS":
                    if not kaleidos_approver["start_date"]:
                        # The flow has been shared, we can set the start time of the approval activity based on the modified_on field
                        start_time = pythonize_iso_timestamp(sh_workflow_details["modified_on"])
                        logger.debug(f"Approver {kaleidos_approver['email']} ready to approve. Syncing start date {start_time} ...")
                        query_string = construct_update_approval_activity_start_date(
                            sig_flow,
                            kaleidos_approver["email"],
                            datetime.fromisoformat(start_time))
                        agent_update(query_string)
                        approvers_changed = True
                elif proc_stat == "REVIEWED":
                    approval_time = pythonize_iso_timestamp(sh_workflow_user["processed_on"])
                    logger.debug(f"Approver {kaleidos_approver['email']} approved. Syncing end date {approval_time} ...")
                    query_string = construct_update_approval_activity_end_date(
                        sig_flow,
                        kaleidos_approver["email"],
                        datetime.fromisoformat(approval_time))
                    agent_update(query_string)
                    approvers_changed = True
                elif proc_stat == "DECLINED":
                    logger.debug(f"Approver {kaleidos_approver['email']} refused. Syncing ...")
                    refusal_time = pythonize_iso_timestamp(sh_workflow_user["processed_on"])
                    query_string = construct_insert_approval_refusal_activity(
                        sig_flow,
                        kaleidos_approver["email"],
                        datetime.fromisoformat(refusal_time))
                    agent_update(query_string)
                    approvers_changed = True
                else:
                    logger.warn(f"Approver {kaleidos_approver['email']} encountered unknown process status {sh_workflow_user['process_status']}. Skipping ...")
            else:
                logger.debug(f"Approver {kaleidos_approver['email']} already has an end date in our db. No syncing needed.")
        else:
            logger.debug(f"Approver with e-mail address {sh_workflow_user['user_email']} not present in Kaleidos metadata: Adding.")
            # insert approver with minimal info. Further details (dates, completion status, ...)
            # will get picked up on a next pass in the SH -> Kaleidos sync direction.
            query_string = construct_insert_approval_activity(sig_flow, sh_workflow_user['user_email'])
            agent_update(query_string)
    return approvers_changed


# Updates the signing activities in the DB based on the
# status of signers we receive from SH
# Returns a boolean that denotes whether an activity has been updated in the DB
def sync_signers_status(sig_flow, sh_workflow_details):
    sh_workflow_users = sh_workflow_details["users"]
    kaleidos_signers = get_signers(sig_flow, agent_query)
    signers_changed = False

    logger.debug(f"Syncing signers status ...")
    for sh_workflow_user in sh_workflow_users:
        if sh_workflow_user["role"] != "SIGNER":
            continue
        proc_stat = sh_workflow_user["process_status"]
        logger.debug(f"Signer {sh_workflow_user['user_email']} has process status {proc_stat}.")
        if proc_stat == "UN_PROCESSED":
            continue # no need to hammer DB for further queries, since we won't be doing anything with the info.
        kaleidos_signer = next(filter(lambda s: s["email"] == sh_workflow_user["user_email"], kaleidos_signers), None)
        if kaleidos_signer:
            if not kaleidos_signer["end_date"]:
                if proc_stat == "IN_PROGRESS":
                    if not kaleidos_signer["start_date"]:
                        start_time = pythonize_iso_timestamp(sh_workflow_details["modified_on"])
                        logger.debug(f"Signer {kaleidos_signer['email']} ready to sign. Syncing start date {start_time} ...")
                        query_string = construct_update_signing_activity_start_date(
                            sig_flow,
                            kaleidos_signer["uri"],
                            datetime.fromisoformat(start_time))
                        agent_update(query_string)
                        signers_changed = True
                elif proc_stat == "SIGNED":
                    logger.debug(f"Signer {kaleidos_signer['email']} signed. Syncing ...")
                    signing_time = pythonize_iso_timestamp(sh_workflow_user["processed_on"])
                    query_string = construct_update_signing_activity_end_date(
                        sig_flow,
                        kaleidos_signer["uri"],
                        datetime.fromisoformat(signing_time))
                    agent_update(query_string)
                    signers_changed = True                    
                elif proc_stat == "DECLINED":
                    logger.debug(f"Signer {kaleidos_signer['email']} refused. Syncing ...")
                    refusal_time = pythonize_iso_timestamp(sh_workflow_user["processed_on"])
                    query_string = construct_insert_signing_refusal_activity(
                        sig_flow,
                        kaleidos_signer["uri"],
                        datetime.fromisoformat(refusal_time))
                    agent_update(query_string)
                    signers_changed = True
                else:
                    logger.warn(f"Unknown process status {sh_workflow_user['process_status']}. Skipping ...")
            else:
                logger.debug(f"Signer {kaleidos_signer['email']} already has an end date in our db. No syncing needed.")
        else:
            logger.debug(f"Signer with e-mail address {sh_workflow_user['user_email']} not present in Kaleidos metadata: ignoring")
    return signers_changed
