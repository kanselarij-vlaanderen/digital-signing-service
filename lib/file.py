from flask import g
from helpers import query
from ..queries.file import construct_get_file_query

SH_SOURCE = "Kaleidos" # TODO https://manuals.ascertia.com/SigningHub-apiguide/default.aspx#pageid=1022

def read_file_bytes(file_uri, max_file_size=None):
    file_query = construct_get_file_query(file_uri)
    file_results = query(file_query)['results']['bindings']
    if not file_results:
        raise Exception("No file found by uri <{}>".format(file_uri))
    file = file_results[0]
    if (max_file_size is not None) and (max_file_size < file["size"]):
        raise Exception("File size {} is greater than maximum allowed size {}.".format(
            file["size"], max_file_size))
    file_path = file["physicalFile"].replace("share://", "/share/")
    with open(file_path, "rb") as f:
        return f.read()

def get_file(file_uri):
    file_query = construct_get_file_query(file_uri)
    file_results = query(file_query)['results']['bindings']
    if not file_results:
        raise Exception("No file found by uri <{}>".format(file_uri))
    file = file_results[0]
    return file

def add_file_to_sh_package(file_uri, sh_package_id):
    file_query = construct_get_file_query(file_uri)
    file_results = query(file_query)['results']['bindings']
    if not file_results:
        raise Exception("No file found by uri <{}>".format(file_uri))
    file = file_results[0]
    data = read_file_bytes(file_uri)
    sh_document = g.sh_session.upload_document(sh_package_id,
                                               data,
                                               file["name"],
                                               SH_SOURCE,
                                               convert_document=False)
    return sh_document
