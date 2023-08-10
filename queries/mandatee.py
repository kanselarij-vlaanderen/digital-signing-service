from datetime import datetime
from string import Template

from escape_helpers import (sparql_escape_datetime, sparql_escape_string,
                            sparql_escape_uri)

from ..config import APPLICATION_GRAPH


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
    ?personMandatee
        persoon:gebruikteVoornaam ?first_name ;
        foaf:familyName ?family_name .
    ?personUser sign:isOndertekenaarVoor ?personMandatee .
    ?personUser foaf:mbox ?mail_uri .
    BIND( REPLACE(STR(?mail_uri), "mailto:", "") AS ?email)
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        mandatee=sparql_escape_uri(mandatee_uri))
