from string import Template
import typing
from flask import g
from signinghub_api_client.client import SigningHubSession
from helpers import generate_uuid, update, logger
from escape_helpers import sparql_escape_uri, sparql_escape_string
from . import exceptions, query_result_helpers, uri, signing_flow
from .mandatee import get_mandatee
from .document import upload_piece_to_sh
from ..config import APPLICATION_GRAPH

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

    signinghub_document_uri, signinghub_package_id, signinghub_document_id = upload_piece_to_sh(piece_uri)
    preparation_activity_id = generate_uuid()
    preparation_activity_uri = uri.resource.preparation_activity(preparation_activity_id)

    query_string = _update_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        signflow=sparql_escape_uri(signflow_uri),
        preparation_activity=sparql_escape_uri(preparation_activity_uri),
        preparation_activity_id=sparql_escape_string(preparation_activity_id),
        sh_document=sparql_escape_uri(signinghub_document_uri),
    )
    update(query_string)

    signers = signing_flow.get_signers(signflow_uri)
    for signer in signers:
        signer = get_mandatee(signer["uri"])
        g.sh_session.add_users_to_workflow(signinghub_package_id, [{
          "user_email": signer["email"],
          "user_name": f"{signer['first_name']} {signer['family_name']}",
          "role": "SIGNER",
          "email_notification": True,
       }])

# optional sign activities to link in case some were already created before sending to SH
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
        ?signing_activity prov:wasInformedBy $preparation_activity .
    }
} WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        OPTIONAL {
            ?signing_activity sign:handtekeningVindtPlaatsTijdens ?sign_subcase .
        }
    }
}
""")
