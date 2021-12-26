from helpers import generate_uuid, query
from ..queries.document import construct_get_document_by_uuid, construct_insert_document
from ..sudo_query import update as sudo_update
from .exceptions import NoQueryResultsException
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
    ins_doc_query_string = construct_insert_document(document_name, virtual_file["uri"], SIGNED_DOCS_GRAPH)
    sudo_update(ins_doc_query_string)
    return doc

def get_document_by_uuid(uuid):
    query_str = construct_get_document_by_uuid(uuid)
    document_results = query(query_str)['results']['bindings']
    if not document_results:
        raise NoQueryResultsException("No document found by uuid '{}'".format(uuid))
    document_uri = document_results[0]["uri"]["value"]
    return document_uri
