from datetime import datetime
from flask import g
from helpers import generate_uuid
from .signing_flow import get_signing_flow, get_pieces
from .document import download_sh_doc_to_kaleidos_doc
from ..config import APPLICATION_GRAPH, KANSELARIJ_GRAPH
from ..queries.document import construct_attach_document_to_previous_version
from ..queries.wrap_up_activity import construct_insert_wrap_up_activity
from ..agent_query import update as agent_update
from ..config import KANSELARIJ_GRAPH, KALEIDOS_RESOURCE_BASE_URI

WRAP_UP_ACTIVITY_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/afrondingsactiviteit/"


def update_signing_flow(signflow_uri: str):
    signing_flow = get_signing_flow(signflow_uri, KANSELARIJ_GRAPH) # TODO, pass in query method, not graph
    sh_package_id = signing_flow["sh_package_id"]
    sh_workflow_details = g.sh_session.get_workflow_details(sh_package_id)
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
                                                                      get_pieces(signflow_uri)[0])
        agent_update(attach_doc_qs)
        wrap_up_uuid = generate_uuid()
        wrap_up_uri = WRAP_UP_ACTIVITY_BASE_URI + wrap_up_uuid
        wrap_up_qs = construct_insert_wrap_up_activity(wrap_up_uri,
                                                       wrap_up_uuid,
                                                       datetime.now(), # TODO: parse the one from sign info instead
                                                       signflow_uri,
                                                       doc["uri"])
        agent_update(wrap_up_qs)

