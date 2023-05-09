from datetime import datetime
from flask import g
from helpers import generate_uuid
from ..queries.file import construct_insert_file_query
from ..agent_query import update as agent_update
from ..config import KANSELARIJ_GRAPH, KALEIDOS_RESOURCE_BASE_URI, TIMEZONE

SH_SOURCE = "Kaleidos" # TODO https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1022

FILE_BASE_URI = KALEIDOS_RESOURCE_BASE_URI + "id/bestand/"
SIGNED_FILES_GRAPH = KANSELARIJ_GRAPH

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
    ins_f_query_string = construct_insert_file_query(virtual_file, physical_file)
    agent_update(ins_f_query_string)
    return virtual_file

def fs_sanitize_filename(filename, replace_char=""):
    # Covers the most common case.
    # In case more is needed, merge https://gitlab.com/jplusplus/sanitize-filename/-/merge_requests/1
    # and use that library instead
    return filename.replace("/", replace_char)
