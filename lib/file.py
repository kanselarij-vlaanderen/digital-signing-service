from datetime import datetime
from pytz import timezone
from flask import g
from helpers import query, generate_uuid
from ..queries.file import construct_get_file_query, \
    construct_get_file_by_id, \
    construct_insert_file_query
from .exceptions import NoQueryResultsException
from ..sudo_query import update as sudo_update
from ..config import KANSELARIJ_GRAPH, KALEIDOS_RESOURCE_BASE_URI

SH_SOURCE = "Kaleidos" # TODO https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1022

TIMEZONE = timezone('Europe/Brussels')

FILE_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/files/"
SIGNED_FILES_GRAPH = KANSELARIJ_GRAPH

def read_file_bytes(file_uri, max_file_size=None):
    file_query = construct_get_file_query(file_uri)
    file_results = query(file_query)['results']['bindings']
    if not file_results:
        raise NoQueryResultsException("No file found by uri <{}>".format(file_uri))
    file = file_results[0]
    if (max_file_size is not None) and (max_file_size < file["size"]["value"]):
        raise NoQueryResultsException("File size {} is greater than maximum allowed size {}.".format(
            file["size"]["value"], max_file_size))
    file_path = file["physicalFile"]["value"].replace("share://", "/share/")
    with open(file_path, "rb") as f:
        return f.read()

def get_file_by_id(file_id):
    file_query = construct_get_file_by_id(file_id)
    file_results = query(file_query)['results']['bindings']
    if not file_results:
        raise NoQueryResultsException("No file found by id '{}'".format(file_id))
    file = {k: v["value"] for k, v in file_results[0].items()}
    return file

def download_sh_doc_to_mu_file(sh_package_id, sh_document_id):
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
    ins_f_query_string = construct_insert_file_query(virtual_file, physical_file, SIGNED_FILES_GRAPH)
    sudo_update(ins_f_query_string)
    return virtual_file
