from string import Template
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string
from .. import exceptions, sparql
from . import uri, GetPieces

def execute(signflow_uri):
    pieces = GetPieces.execute(signflow_uri)
    if pieces is None:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    if len(pieces) == 0:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no related pieces.")

    if len(pieces) != 1:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has multiple pieces.")

    status = pieces[0]["status"]
    if status != "marked":
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no unprepared piece.")

    piece_uri = pieces[0]["uri"]

    preparation_activity_id = generate_uuid()
    preparation_activity_uri = uri.resource.preparation_activity(preparation_activity_id)

    signinghub_package_id = generate_uuid()
    signinghub_document_id = generate_uuid()
    signinghub_document = uri.resource.signinghub_document(signinghub_package_id, signinghub_document_id)

    template = Template(sparql.relative_file("prepare.sparql"))
    query_command = template.safe_substitute(
        graph=sparql_escape_uri(uri.graph.sign),
        signflow=sparql_escape_uri(signflow_uri),
        preparation_activity=sparql_escape_uri(preparation_activity_uri),
        preparation_activity_id=sparql_escape_string(preparation_activity_id),
        piece=sparql_escape_uri(piece_uri),
        sh_document=sparql_escape_uri(signinghub_document),
        sh_document_id=sparql_escape_string(signinghub_document_id),
        sh_package_id=sparql_escape_string(signinghub_package_id),
    )
    sparql.update(query_command)
