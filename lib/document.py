from datetime import datetime
from pytz import timezone
from flask import g
from helpers import query, generate_uuid
from ..queries.document import construct_get_file_for_document, construct_insert_document
from ..sudo_query import update as sudo_update
from ..queries.file import construct_insert_file_query
from .exceptions import NoQueryResultsException

TIMEZONE = timezone('Europe/Brussels')

APPLICATION_GRAPH = "http://mu.semte.ch/application"
SIGNED_DOCS_GRAPH = "http://mu.semte.ch/graphs/organizations/kanselarij"

FILE_BASE_URI = "http://kanselarij.vo.data.gift/id/files/"

def get_file_for_document(document_uri):
    query_string = construct_get_file_for_document(document_uri, file_mimetype="application/pdf")
    file_results = query(query_string)['results']['bindings']
    if not file_results:
        raise NoQueryResultsException("No pdf-file found for document by uri <{}>".format(document_uri))
    file = file_results[0]
    return file

def download_sh_doc_to_kaleidos_doc(sh_package_id, sh_document_id, document_name):
    file_bytes = g.sh_session.download_document(sh_package_id, sh_document_id)
    physical_file = {
        "extension": "pdf",
        "uuid": generate_uuid()
    } # Other properties taken form virtual file
    physical_file["name"] = physical_file["uuid"] + "." + physical_file["extension"]
    physical_path = "/share/{}".format(physical_file["name"])
    physical_file["uri"] = physical_path.replace("/share/", "share://")
    with open(physical_path, "wb") as f:
        f.write(file_bytes)
    virtual_file = {
        "created": datetime.now(TIMEZONE),
        "extension": "pdf",
        "uuid": generate_uuid(),
        "mimetype": "application/pdf",
        "size": len(file_bytes)
    }
    virtual_file["uri"] = FILE_BASE_URI + virtual_file["uuid"]
    virtual_file["name"] = virtual_file["uuid"] + "." + virtual_file["extension"]
    ins_f_query_string = construct_insert_file_query(virtual_file, physical_file, SIGNED_DOCS_GRAPH)
    sudo_update(ins_f_query_string)
    ins_doc_query_string = construct_insert_document(document_name, virtual_file["uri"], SIGNED_DOCS_GRAPH)
    sudo_update(ins_doc_query_string)
    return virtual_file

