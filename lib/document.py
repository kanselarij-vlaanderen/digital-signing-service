from helpers import generate_uuid, query
from ..queries.document import construct_insert_document
from ..agent_query import update as agent_update
from .file import download_sh_doc_to_mu_file
from ..config import KANSELARIJ_GRAPH, KALEIDOS_RESOURCE_BASE_URI

SIGNED_DOCS_GRAPH = KANSELARIJ_GRAPH

DOC_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/stuk/"

def download_sh_doc_to_kaleidos_doc(sh_package_id, sh_document_id, document_name):
    virtual_file = download_sh_doc_to_mu_file(sh_package_id, sh_document_id)
    doc = {
        "uuid": generate_uuid(),
        "name": document_name
    }
    doc["uri"] = DOC_BASE_URI + doc["uuid"]
    ins_doc_query_string = construct_insert_document(document_name, virtual_file["uri"])
    agent_update(ins_doc_query_string)
    return doc
