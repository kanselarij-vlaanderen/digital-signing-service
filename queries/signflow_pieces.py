import typing
from string import Template
from escape_helpers import sparql_escape_uri, sparql_escape_string
from ..lib import uri

def construct_signflow_pieces_query(
    signflow_uri: str,
    piece_uri: typing.Optional[str] = None):
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT DISTINCT ?signflow
    ?piece ?piece_id
    ?activity_type
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .

        ?piece a dossier:Stuk ;
            mu:uuid ?piece_id .

        ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase .
        ?marking_activity a sign:Markeringsactiviteit .
        ?marking_activity sign:gemarkeerdStuk ?piece .
        ?piece a dossier:Stuk ;
            mu:uuid ?piece_id .

        OPTIONAL {
            ?preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
            ?preparation_activity a sign:Voorbereidingsactiviteit .
            OPTIONAL {
                ?preparation_activity sign:voorbereidingGenereert ?sh_document .
                ?sh_document a sh:Document ;
                prov:hadPrimarySource ?piece .

                ?sh_document prov:hadPrimarySource ?piece .
                ?sh_document sh:packageId ?sh_package_id ;
                    sh:documentId ?sh_document_id .
            }
        }

        OPTIONAL {
      		?signing_activity sign:handtekeningVindtPlaatsTijdens ?sign_subcase .
      		?signing_activity a sign:Handtekenactiviteit .
        	?signing_activity prov:wasInformedBy ?preparation_activity .
    	}
    }

    BIND (IF (BOUND (?signing_activity), sign:Handtekenactiviteit,
        IF (BOUND (?preparation_activity), sign:Voorbereidingsactiviteit,
        IF (BOUND (?marking_activity), sign:Markeringsactiviteit, ?NULL))) AS ?activity_type)

    VALUES ?signflow { $signflow }
    OPTIONAL { VALUES ?piece { $piece } }
}
""")

    query_sparql = query_template.safe_substitute({
        "graph": sparql_escape_uri(uri.graph.application),
        "signflow": sparql_escape_uri(signflow_uri),
        "piece": sparql_escape_string(piece_uri) if piece_uri else ''
    })

    return query_sparql