import helpers
from .... import db, exceptions
from ....db import uri, string, file_rel
from ... import queries, URI

def prepare(signflow_uri):
    exists = queries.signflow_exists(signflow_uri)
    if not exists:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    pieces = queries.signflow_pieces(signflow_uri)
    if not pieces:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no related pieces.")

    if len(pieces) != 1:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has multiple pieces.")

    status = pieces[0]["status"]
    if status != "marked":
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no unprepared piece.")

    piece_uri = pieces[0]["uri"]

    preparation_activity_id = helpers.generate_uuid()
    preparation_activity_uri = URI.resource.preparation_activity(preparation_activity_id)

    signinghub_package_id = helpers.generate_uuid()
    signinghub_document_id = helpers.generate_uuid()
    signinghub_document = URI.resource.signinghub_document(signinghub_package_id, signinghub_document_id)

    db.update(file_rel("prepare.sparql"), {
        "graph": uri(URI.graph.sign),
        "signflow": uri(signflow_uri),
        "preparation_activity": uri(preparation_activity_uri),
        "preparation_activity_id": string(preparation_activity_id),
        "piece": uri(piece_uri),
        "sh_document": uri(signinghub_document),
        "sh_document_id": string(signinghub_document_id),
        "sh_package_id": string(signinghub_package_id),
    })
