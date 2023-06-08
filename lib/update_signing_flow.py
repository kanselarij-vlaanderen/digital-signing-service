from datetime import datetime
from flask import g
from helpers import generate_uuid, logger
from ..authentication import ensure_signinghub_machine_user_session
from .signing_flow import get_signing_flow, get_signers, get_pieces, get_creator
from .document import download_sh_doc_to_kaleidos_doc
from ..queries.document import construct_attach_document_to_unsigned_version
from ..queries.wrap_up_activity import construct_insert_wrap_up_activity
from ..queries.signing_flow_signers import construct_update_signing_activity_end_date
from ..agent_query import update as agent_update, query as agent_query
from ..config import KALEIDOS_RESOURCE_BASE_URI

WRAP_UP_ACTIVITY_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/afrondingsactiviteit/"


def update_signing_flow(signflow_uri: str):
    signing_flow = get_signing_flow(signflow_uri, agent_query)
    creator = get_creator(signflow_uri, agent_query)
    ensure_signinghub_machine_user_session(creator["email"])
    sh_package_id = signing_flow["sh_package_id"]
    sh_workflow_details = g.sh_session.get_workflow_details(sh_package_id)
    logger.debug(f'Signing flow {signflow_uri}, workflow status {sh_workflow_details["workflow"]["workflow_status"]}')
    if sh_workflow_details["workflow"]["workflow_status"] == "DRAFT":
        # TODO
        pass
    if sh_workflow_details["workflow"]["workflow_status"] == "IN_PROGRESS":
        sync_signers_status(signflow_uri, sh_workflow_details)
        # TODO approvers
        pass
    elif sh_workflow_details["workflow"]["workflow_status"] == "COMPLETED":
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

def sync_signers_status(sig_flow, sh_workflow_details):
    sh_workflow_users = sh_workflow_details["users"]
    kaleidos_signers = get_signers(sig_flow, agent_query)
    logger.debug(f"Syncing signers status ...")
    for sh_workflow_user in sh_workflow_users:
        proc_stat = sh_workflow_user["process_status"]
        logger.debug(f"Signer {sh_workflow_user['user_email']} has process status {proc_stat}.")
        if proc_stat == "UN_PROCESSED":
            continue # no need to hammer DB for further queries, since we won't be doing anything with the info.
        kaleidos_signer = next(filter(lambda s: s["email"] == sh_workflow_user["user_email"], kaleidos_signers), None)
        if kaleidos_signer:
            if not kaleidos_signer["end_date"]:
                # elif proc_stat == "IN_PROGRESS": # SHARED
                if proc_stat == "SIGNED": # "REVIEWED",
                    logger.info(f"Signer {kaleidos_signer['email']} signed. Syncing ...")
                    signing_time = sh_workflow_user["processed_on"]
                    query_string = construct_update_signing_activity_end_date(
                        sig_flow,
                        kaleidos_signer["uri"],
                        datetime.fromisoformat(signing_time))
                    agent_update(query_string)
                # elif proc_stat == "DECLINED":
                else:
                    logger.warn(f"Unknown process status {sh_workflow_user['process_status']}. Skipping ...")
            else:
                logger.info(f"Signer {kaleidos_signer['email']} already has an end date in our db. No syncing needed.")
        else:
            logger.info(f"Signer with e-mail address {kaleidos_signer['email']} not present in Kaleidos metadata: ignoring")
