from string import Template

from escape_helpers import sparql_escape_uri

from ..config import APPLICATION_GRAPH


def construct(signflow_uri: str):
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT DISTINCT ?piece ?piece_id ?sh_document_id
WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?marking_activity a sign:Markeringsactiviteit ;
            sign:markeringVindtPlaatsTijdens ?sign_subcase ;
            sign:gemarkeerdStuk ?piece .
        ?piece a dossier:Stuk ;
            mu:uuid ?piece_id .

        OPTIONAL {
            ?preparation_activity a sign:Voorbereidingsactiviteit ;
                sign:voorbereidingVindtPlaatsTijdens ?sign_subcase ;
                sign:voorbereidingGenereert ?signinghub_doc .
            ?signinghub_doc a signinghub:Document ;
                prov:hadPrimarySource ?piece ;
                signinghub:documentId ?sh_document_id .
        }

    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        signflow=sparql_escape_uri(signflow_uri)
    )
