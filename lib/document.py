from ..queries.document import construct_get_file_for_document
from helpers import query

APPLICATION_GRAPH = "http://mu.semte.ch/application"

def get_file_for_document(document_uri):
    query_string = construct_get_file_for_document(document_uri, file_mimetype="application/pdf")
    file_results = query(query_string)['results']['bindings']
    if not file_results:
        raise Exception("No pdf-file found for document by uri <{}>".format(document_uri))
    file = file_results[0]
    return file
