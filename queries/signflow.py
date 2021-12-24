from string import Template
from escape_helpers import sparql_escape_uri, sparql_escape_string
from ..config import APPLICATION_GRAPH

def construct(signflow_uri: str):
    return __signflow_query_template.substitute(
      graph=sparql_escape_uri(APPLICATION_GRAPH),
      signflow=sparql_escape_uri(signflow_uri),
      sh_package_id='',
    )

def construct_by_signinghub_id(sh_package_id: str):
    return __signflow_query_template.substitute(
      graph=sparql_escape_uri(APPLICATION_GRAPH),
      signflow='',
      sh_package_id=sparql_escape_string(sh_package_id),
    )

# matches on ?signflow or ?sh_package_id, depending on the provided and empty parameter.
__signflow_query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signflow ?signflow_id ?piece ?sh_document ?sh_package_id
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            mu:uuid ?signflow_id .
        ?signflow sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?sign_subcase ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .
        ?preparation_activity a sign:Voorbereidingsactiviteit .
        ?preparation_activity sign:voorbereidingGenereert ?sh_document .
        ?sh_document a sh:Document .
        ?sh_document sh:packageId ?sh_package_id .
    }

    OPTIONAL { VALUES ?signflow { $signflow } }
    OPTIONAL { VALUES ?sh_package_id { $sh_package_id } }
}
""")
