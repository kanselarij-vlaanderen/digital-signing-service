from string import Template
from datetime import datetime, timedelta
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime

APPLICATION_GRAPH = "http://mu.semte.ch/application"

SIGNING_ACT_TYPE_URI = "http://mu.semte.ch/vocabularies/ext/publicatie/Handtekenactiviteit"

def construct_get_mandatee_by_id(mandatee_id, graph=APPLICATION_GRAPH):
    query_template = Template("""
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>

SELECT DISTINCT (?mandatee as ?uri)
WHERE {
    GRAPH $graph {
        ?mandatee a mandaat:Mandataris ;
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
        $mandatee a mandaat:Mandataris ;
            mandaat:isBestuurlijkeAliasVan ?person .
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

def construct_get_mandatee_by_email(mandatee_email, graph=APPLICATION_GRAPH):
    mail_uri = "mailto:{}".format(mandatee_email)
    maximal_end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) # Today
    # Sometimes a mandatee needs to sign some last docs a couple of days after the end of the mandate
    maximal_end_date = maximal_end_date - timedelta(days=30)
    query_template = Template("""
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>

SELECT ?mandatee
WHERE {
    GRAPH $graph {
        ?mandatee a mandaat:Mandataris ;
            mandaat:isBestuurlijkeAliasVan ?person ;
            mandaat:einde ?end_date ;
            mandaat:start ?start_date .
        ?person foaf:mbox $mail_uri .
        FILTER(?start_date < NOW())
        FILTER(?end_date > $end_date)
    }
}
ORDER BY DESC(?end_date)
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        mail_uri=sparql_escape_uri(mail_uri),
        end_date=sparql_escape_datetime(maximal_end_date))

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
        type=sparql_escape_uri(SIGNING_ACT_TYPE_URI),
        signing_prep=sparql_escape_uri(signing_prep_uri))

