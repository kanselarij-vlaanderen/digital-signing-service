from string import Template
from escape_helpers import sparql_escape_uri, sparql_escape_string

APPLICATION_GRAPH = "http://mu.semte.ch/application"

PUB_FLOW_TYPE_URI = "http://example.com/concept/123"
SIGNING_SUBC_TYPE_URI = "http://example.com/concept/123"

def construct_get_subcase_from_pub_flow_id(pub_flow_id,
                                           graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>

SELECT DISTINCT (?signing_subcase AS ?uri)
WHERE {
    GRAPH $graph {
        ?pub_flow a $pub_flow_type ;
            mu:uuid $pub_flow_id .
        ?signing_subcase a dossier:Procedurestap ;
            dct:type $subcase_type .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        pub_flow_type=sparql_escape_uri(PUB_FLOW_TYPE_URI),
        pub_flow_id=sparql_escape_string(pub_flow_id),
        subcase_type=sparql_escape_uri(SIGNING_SUBC_TYPE_URI))
