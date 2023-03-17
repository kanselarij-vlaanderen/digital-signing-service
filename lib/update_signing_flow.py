from flask import g
from .document import download_sh_doc_to_kaleidos_doc
def update_signing_flow(signflow_uri: str):
    signing_flow = get_signing_flow(signflow_uri, KANSELARIJ_GRAPH)
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
