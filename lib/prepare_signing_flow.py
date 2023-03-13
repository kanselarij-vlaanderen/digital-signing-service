from string import Template
import typing
from signinghub_api_client.client import SigningHubSession
from helpers import generate_uuid, query, update
from escape_helpers import sparql_escape_uri, sparql_escape_string
from . import exceptions, query_result_helpers, uri, signing_flow
from ..config import APPLICATION_GRAPH

SH_SOURCE = "Kaleidos"

# TODO:
# validation:
# - document is not uploaded yet
def prepare_signing_flow(signinghub_session: SigningHubSession,
                     signflow_uri: str,
                     piece_uris: typing.List[str]):
    if len(piece_uris) == 0:
        raise exceptions.InvalidArgumentException(f"No piece to add specified.")
    if len(piece_uris) > 1:
        raise exceptions.InvalidArgumentException(f"Signflow can only add 1 piece.")
    piece_uri = piece_uris[0]

    pieces = signing_flow.get_pieces(signflow_uri)
    piece = query_result_helpers.ensure_1(pieces)
    if piece["uri"] != piece_uri:
        raise exceptions.InvalidStateException(f"Piece {piece_uri} is not associated to signflow {signflow_uri}.")

    get_file_query_string = _query_file_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        piece=sparql_escape_uri(piece_uri),
    )
    file_result = query(get_file_query_string)
    file_records = query_result_helpers.to_recs(file_result)
    file_record = query_result_helpers.ensure_1(file_records)
    file_name = file_record["piece_name"] + "." + file_record["file_extension"]
    file_path = file_record["file_path"]

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
        file_name,
        SH_SOURCE,
        convert_document=False)
    signinghub_document_id = signinghub_document["documentid"]

    sh_document_muid = generate_uuid()
    signinghub_document_uri = uri.resource.signinghub_document(signinghub_package_id, signinghub_document_id)
    query_string = _update_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        signflow=sparql_escape_uri(signflow_uri),
        preparation_activity=sparql_escape_uri(preparation_activity_uri),
        preparation_activity_id=sparql_escape_string(preparation_activity_id),
        piece=sparql_escape_uri(piece_uri),
        sh_document=sparql_escape_uri(signinghub_document_uri),
        sh_document_muid=sparql_escape_string(sh_document_muid),
        sh_document_id=sparql_escape_string(str(signinghub_document_id)),
        sh_package_id=sparql_escape_string(str(signinghub_package_id)),
    )
    update(query_string)

_query_file_template = Template("""
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dbpedia: <http://dbpedia.org/ontology/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX nie: <http://www.semanticdesktop.org/ontologies/2007/01/19/nie#>

SELECT ?piece_name ?file ?file_extension ?file_path
WHERE {
    GRAPH $graph {
        $piece a dossier:Stuk ;
            dct:title ?piece_name .

        $piece ext:file ?file .
        ?file dbpedia:fileExtension ?file_extension ;
             ^nie:dataSource ?file_path .
    }
}
""")

_update_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        $preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
        $preparation_activity a sign:Voorbereidingsactiviteit ;
            mu:uuid $preparation_activity_id .
        $preparation_activity sign:voorbereidingGenereert $sh_document .
        $sh_document a sh:Document ;
            mu:uuid $sh_document_muid ;
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