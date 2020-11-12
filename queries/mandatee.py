from string import Template
from datetime import datetime
from pytz import timezone
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime

APPLICATION_GRAPH = "http://mu.semte.ch/application"

def construct_get_mandatee(mandatee_uri, graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>

SELECT ?email ?first_name ?family_name
WHERE {
    GRAPH $graph {
        $mandatee a mandaat:Mandataris .
            mandatee mandaat:isBestuurlijkeAliasVan ?person .
        OPTIONAL { ?person foaf:firstName ?first_name }
        OPTIONAL { ?person foaf:familyName ?family_name }
        OPTIONAL {
            ?person foaf:mbox ?mail_uri .
            BIND( REPLACE(STR(?mail_uri), "mailto:", "") AS ?email)
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        mandatee=sparql_escape_uri(mandatee_uri))


