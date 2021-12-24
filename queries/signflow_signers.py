from string import Template
from escape_helpers import sparql_escape_uri
from ..lib import uri

def construct(signflow_uri: str) -> str:
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signing_activity ?start_date ?end_date ?signer ?signer_id
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid .
        ?signflow sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?sign_subcase ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?signing_activity a sign:Handtekenactiviteit .
        ?signing_activity dossier:Activiteit.startdatum ?start_date .
        ?signing_activity dossier:Activiteit.einddatum ?end_date .
        ?signing_activity sign:ondertekenaar ?signer .
        ?signer a mandaat:Mandataris .
        ?signer mu:uuid ?signer_id .
    }

    VALUES ?signflow { $signflow }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(uri.graph.application),
        signflow=sparql_escape_uri(signflow_uri)
    )
