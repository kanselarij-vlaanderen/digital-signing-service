from string import Template
import helpers
from signinghub_api_client.client import SigningHubSession
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string
from .. import exceptions, sparql
from . import uri, GetPieces

SH_SOURCE = "Kaleidos"

def execute(signflow_uri, signinghub_session: SigningHubSession):
    pieces = GetPieces.execute(signflow_uri)
    if pieces is None:
        raise exceptions.ResourceNotFoundException(signflow_uri)
    
    if len(pieces) == 0:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no related pieces.")

    if len(pieces) != 1:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has multiple pieces.")

    piece = pieces[0]
    status = piece["status"]
    if status != "marked":
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no unprepared piece.")

    piece_uri = piece["uri"]
    piece_name = piece["name"] + ".pdf"
    file_path = piece["file_path"]
    file_path = file_path.replace("share://", "/share/")

    with open(file_path, "rb") as f:
        file_content = f.read()

    preparation_activity_id = generate_uuid()
    preparation_activity_uri = uri.resource.preparation_activity(preparation_activity_id)

    signinghub_package = signinghub_session.add_package({
        # package_name: "New Package", # Defaults to "Undefined"
        "workflow_mode": "ONLY_OTHERS" # OVRB staff who prepare the flows will never sign
    })
    signinghub_package_id = signinghub_package["package_id"]
    signinghub_document = signinghub_session.upload_document(
        signinghub_package_id,
        file_content,
        piece_name,
        SH_SOURCE,
        convert_document=False)
    signinghub_document_id = signinghub_document["documentid"]
    signinghub_document_uri = uri.resource.signinghub_document(signinghub_package_id, signinghub_document_id)

    update_command = _update_template.safe_substitute(
        graph=sparql_escape_uri(uri.graph.sign),
        signflow=sparql_escape_uri(signflow_uri),
        preparation_activity=sparql_escape_uri(preparation_activity_uri),
        preparation_activity_id=sparql_escape_string(preparation_activity_id),
        piece=sparql_escape_uri(piece_uri),
        sh_document=sparql_escape_uri(signinghub_document_uri),
        sh_document_id=sparql_escape_string(str(signinghub_document_id)),
        sh_package_id=sparql_escape_string(str(signinghub_package_id)),
    )
    sparql.update(update_command)


_update_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        $preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
        $preparation_activity a sign:Voorbereidingsactiviteit ;
            mu:uuid $preparation_activity_id .
        $preparation_activity sign:voorbereidingGenereert $sh_document .
        $sh_document a sh:Document ;
            sh:packageId $sh_package_id ;
            sh:documentId $sh_document_id ;
            prov:hadPrimarySource $piece .
    }
} WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
    }
}
""")