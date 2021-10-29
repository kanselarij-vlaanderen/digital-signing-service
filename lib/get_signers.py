from string import Template
from helpers import query
from escape_helpers import sparql_escape_string, sparql_escape_uri
from . import exceptions, helpers, uri, validate, get_pieces

def execute(signflow_uri: str, piece_uri: str):
    validate.ensure_signflow_exists(signflow_uri)
    validate.ensure_piece_exists(piece_uri)
   
    pieces = get_pieces.execute(signflow_uri)
    piece = helpers.ensure_1(pieces)
    if piece["uri"] != piece_uri:
        raise exceptions.InvalidStateException(f"Piece <{piece_uri}> is not linked to signflow <{signflow_uri}>.")

    query_command = _query_template.safe_substitute(
        graph=sparql_escape_uri(uri.graph.sign),
        signflow=sparql_escape_uri(signflow_uri),
        piece=sparql_escape_uri(piece_uri)
    )
    result = query(query_command)
    records = helpers.to_recs(result)
    signers = [{
        "uri": r["signer"],
        "id": r["signer_id"],
    } for r in records]

    return signers

_query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <https://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signer ?signer_id
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?sign_subcase ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?signing_activity a sign:Handtekenactiviteit .
        
        ?signing_activity prov:wasInformedBy ?preparation_activity .
        ?preparation_activity sign:voorbereidingGenereert ?signinghub_document .
        ?signinghub_document prov:hadPrimarySource ?piece .

        ?signing_activity sign:ondertekenaar ?signer .
        ?signer a mandaat:Mandataris .
        ?signer mu:uuid ?signer_id .
    }

    VALUES ?piece { $piece }
    VALUES ?signflow { $signflow }
}
""")
