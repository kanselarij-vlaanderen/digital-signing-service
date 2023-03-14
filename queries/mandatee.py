from string import Template
from datetime import datetime, timedelta
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_datetime
from ..config import APPLICATION_GRAPH

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

def construct_get_mandatee(mandatee_uri):
    # Note: Can only be ran through mu-auth, data is spread over multiple graphs
    query_template = Template("""
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX persoon: <https://data.vlaanderen.be/ns/persoon#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

SELECT DISTINCT ?email ?first_name ?family_name
WHERE {
    $mandatee a mandaat:Mandataris ;
        mandaat:isBestuurlijkeAliasVan ?personMandatee .
    ?personMandatee persoon:gebruikteVoornaam ?first_name }
    ?personMandatee foaf:familyName ?family_name }
    ?personUser sign:isOndertekenaarVoor ?personMandatee .
    ?personUser foaf:mbox ?mail_uri .
    BIND( REPLACE(STR(?mail_uri), "mailto:", "") AS ?email)
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        mandatee=sparql_escape_uri(mandatee_uri))

def construct_get_active_mandatee_by_email(mandatee_email):
    mail_uri = "mailto:{}".format(mandatee_email)
    maximal_end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) # Today
    # Sometimes a mandatee needs to sign some last docs a couple of days after the end of the mandate
    maximal_end_date = maximal_end_date - timedelta(days=30)
    # Note: Can only be ran through mu-auth, data is spread over multiple graphs
    query_template = Template("""
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

SELECT DISTINCT ?mandatee
WHERE {
    ?mandatee a mandaat:Mandataris ;
        mandaat:isBestuurlijkeAliasVan ?personMandatee ;
        mandaat:start ?start_date .
    ?personUser foaf:mbox $mail_uri .
    ?personUser sign:isOndertekenaarVoor ?personMandatee .
    FILTER(?start_date < NOW())
    OPTIONAL {
        ?mandatee mandaat:einde ?end_date .
        FILTER(?end_date > $end_date)
    }
}
ORDER BY DESC(?start_date) DESC(?end_date)
""")
    return query_template.substitute(
        mail_uri=sparql_escape_uri(mail_uri),
        end_date=sparql_escape_datetime(maximal_end_date))
