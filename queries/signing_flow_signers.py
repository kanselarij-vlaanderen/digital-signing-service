from string import Template
from escape_helpers import sparql_escape_uri
from ..config import APPLICATION_GRAPH

def construct(signflow_uri: str) -> str:
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signing_activity ?start_date ?end_date ?signer ?signer_id
WHERE {
    BIND($signflow AS ?signflow)
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?signing_activity a sign:Handtekenactiviteit ;
            sign:ondertekenaar ?signer .
        ?signer a mandaat:Mandataris ;
            mu:uuid ?signer_id .
        OPTIONAL {
            ?signing_activity dossier:Activiteit.startdatum ?start_date .
        }
        OPTIONAL {
            ?signing_activity dossier:Activiteit.einddatum ?end_date .
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        signflow=sparql_escape_uri(signflow_uri)
    )
