from string import Template
from datetime import datetime
from escape_helpers import sparql_escape_uri, sparql_escape_string,sparql_escape_datetime
from ..config import APPLICATION_GRAPH

def construct_insert_wrap_up_activity(wrap_up_uri: str,
                                      wrap_up_id: str,
                                      wrap_up_end: datetime,
                                      signflow_uri: str,
                                      signed_document_uri: str
                                      ):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX prov: <http://www.w3.org/ns/prov#>

INSERT {
    $wrap_up_activity
        a sign:Afrondingsactiviteit ;
        mu:uuid $wrap_up_activity_id ;
        dossier:Activiteit.einddatum $wrap_up_end ;
        sign:afrondingVindtPlaatsTijdens ?signing_subcase ;
        prov:wasInformedBy ?signing_activity ;
        sign:getekendStuk $signed_document .
}
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?signing_subcase .
    ?signing_subcase ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
}
""")
    return query_template.substitute(
        wrap_up_activity=sparql_escape_uri(wrap_up_uri),
        wrap_up_activity_id=sparql_escape_string(wrap_up_id),
        wrap_up_end=sparql_escape_datetime(wrap_up_end),
        signed_document=sparql_escape_uri(signed_document_uri),
        signflow=sparql_escape_uri(signflow_uri)
    )
