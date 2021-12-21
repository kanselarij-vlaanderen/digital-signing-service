from pytz import timezone
from helpers import query, generate_uuid
from ..queries.document import construct_get_file_for_document, construct_insert_document
from ..sudo_query import update as sudo_update
from .file import download_sh_doc_to_mu_file
from .exceptions import NoQueryResultsException

TIMEZONE = timezone('Europe/Brussels')

APPLICATION_GRAPH = "http://mu.semte.ch/application"
SIGNED_DOCS_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"

DOC_BASE_URI = "http://kanselarij.vo.data.gift/id/stukken/"

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
