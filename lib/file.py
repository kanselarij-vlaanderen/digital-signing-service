from helpers import query
from ..queries.file import construct_get_file_query

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
