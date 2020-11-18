from string import Template
from datetime import datetime
from pytz import timezone
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime

APPLICATION_GRAPH = "http://mu.semte.ch/application"

SIGNING_ACT_TYPE_URI = "http://example.com/concept/123"

def construct_get_mandatee_by_id(mandatee_id, graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>

SELECT DISTINCT (?mandatee as ?uri)
WHERE {
    GRAPH $graph {
        $mandatee a mandaat:Mandataris ;
            mu:uuid $uuid .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        uuid=sparql_escape_string(mandatee_id))

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

def construct_get_signing_mandatees(signing_prep_uri,
                                    graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>

SELECT DISTINCT (?mandatee as ?uri) ?uuid
WHERE {
    GRAPH $graph {
        ?signing a prov:Activity ;
            dct:type $type ;
            prov:wasInformedBy $signing_prep ;
            prov:qualifiedAssociation ?mandatee .
        ?mandatee a mandaat:Mandataris ;
            mu:uuid ?uuid .
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        type=sparql_escape_string(SIGNING_ACT_TYPE_URI),
        signing_prep=sparql_escape_uri(signing_prep_uri))

