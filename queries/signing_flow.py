from string import Template
from escape_helpers import sparql_escape_uri, sparql_escape_string
from ..config import APPLICATION_GRAPH

def construct(signflow_uri: str, graph=APPLICATION_GRAPH):
    return __signflow_query_template.substitute(
      graph=sparql_escape_uri(graph),
      signflow=sparql_escape_uri(signflow_uri),
      sh_package_id='',
    )

def construct_by_signinghub_id(sh_package_id: str):
    return __signflow_query_template.substitute(
      graph=sparql_escape_uri(APPLICATION_GRAPH),
      signflow='',
      sh_package_id=sparql_escape_string(sh_package_id),
    )

def construct_by_mu_uuid(uuid: str):
    return __signflow_by_uuid_query_template.substitute(
      graph=sparql_escape_uri(APPLICATION_GRAPH),
      uuid=sparql_escape_string(uuid),
    )


# matches on ?signflow or ?sh_package_id, depending on the provided and empty parameter.
__signflow_query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signflow ?signflow_id ?piece ?sh_document ?sh_package_id
WHERE {
    OPTIONAL { VALUES ?signflow { $signflow } }
    OPTIONAL { VALUES ?sh_package_id { $sh_package_id } }
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            mu:uuid ?signflow_id .
        ?signflow sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .
        ?preparation_activity a sign:Voorbereidingsactiviteit ;
            sign:voorbereidingGenereert ?sh_document .
        ?sh_document a sh:Document ;
            sh:packageId ?sh_package_id .
    }
}
""")

__signflow_by_uuid_query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

SELECT ?signflow
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            mu:uuid $uuid .
    }
}
""")


