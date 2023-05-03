from datetime import datetime
from flask import g
from helpers import generate_uuid, logger
from ..authentication import ensure_signinghub_machine_user_session
from .signing_flow import get_signing_flow, get_pieces, get_creator
from .document import download_sh_doc_to_kaleidos_doc
from ..queries.document import construct_attach_document_to_previous_version
from ..queries.wrap_up_activity import construct_insert_wrap_up_activity
from ..agent_query import update as agent_update, query as agent_query
from ..config import KALEIDOS_RESOURCE_BASE_URI

WRAP_UP_ACTIVITY_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/afrondingsactiviteit/"


def update_signing_flow(signflow_uri: str):
    signing_flow = get_signing_flow(signflow_uri, agent_query)
    creator = get_creator(signflow_uri, agent_query)
    ensure_signinghub_machine_user_session(creator["email"])
    sh_package_id = signing_flow["sh_package_id"]
    sh_workflow_details = g.sh_session.get_workflow_details(sh_package_id)
    logger.info(f'Signing flow {signflow_uri}, workflow status {sh_workflow_details["workflow"]["workflow_status"]}')
    if sh_workflow_details["workflow"]["workflow_status"] == "DRAFT":
        # TODO
        pass
    if sh_workflow_details["workflow"]["workflow_status"] == "IN_PROGRESS":
        # TODO
        pass
    elif sh_workflow_details["workflow"]["workflow_status"] == "COMPLETED":
        # TODO: check if everyone signed/approved/reviewed/... (didnt reject)
        doc = download_sh_doc_to_kaleidos_doc(sh_workflow_details["package_id"],
                                        sh_workflow_details["documents"][0]["document_id"],
                                        "getekend document" # TODO: same name as exising doc
                                        )

        attach_doc_qs = construct_attach_document_to_previous_version(doc["uri"],
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
