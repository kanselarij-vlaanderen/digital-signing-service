from string import Template
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_datetime
from ..config import APPLICATION_GRAPH

HANDTEKENACTIVITEIT_RESOURCE_BASE_URI = "http://themis.vlaanderen.be/id/handtekenactiviteit/"

def construct(signflow_uri: str) -> str:
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT ?signing_activity ?start_date ?end_date ?signer ?signer_id ?email
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?sign_subcase .
    ?sign_subcase a sign:HandtekenProcedurestap ;
        ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
    ?signing_activity a sign:Handtekenactiviteit ;
        sign:ondertekenaar ?signer .
    ?signer a mandaat:Mandataris ;
        mu:uuid ?signer_id ;
        mandaat:isBestuurlijkeAliasVan ?personMandatee .
    ?personUser sign:isOndertekenaarVoor ?personMandatee ;
        foaf:mbox ?mail_uri .
    BIND(REPLACE(STR(?mail_uri), "mailto:", "") AS ?email)
    OPTIONAL {
        ?signing_activity dossier:Activiteit.startdatum ?start_date .
    }
    OPTIONAL {
        ?signing_activity dossier:Activiteit.einddatum ?end_date .
    }
}
""")
    return query_template.substitute(
        signflow=sparql_escape_uri(signflow_uri)
    )

def construct_add_signer(signflow_uri, mandatee_uri):
    uuid = generate_uuid()
    uri = HANDTEKENACTIVITEIT_RESOURCE_BASE_URI + uuid
    # Optional preparation activity. Depending on if the document has already been sent to
    # signinghub, the preparation activity won't/will be there.
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    $signing_activity a sign:Handtekenactiviteit ;
        mu:uuid $signing_activity_id ;
        sign:handtekeningVindtPlaatsTijdens ?sign_subcase ;
        prov:wasInformedBy ?preparation_activity ;
        sign:ondertekenaar $signer .
}
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?sign_subcase .
    OPTIONAL {
        ?preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
    }
}
""")
    return query_template.substitute(
        signing_activity=sparql_escape_uri(uri),
        signing_activity_id=sparql_escape_string(uuid),
        signer=sparql_escape_uri(mandatee_uri),
        signflow=sparql_escape_uri(signflow_uri))


def construct_update_signing_activity_end_date(signflow_uri: str, mandatee_uri, end_date, graph=APPLICATION_GRAPH) -> str:
    # TODO: probably needs e-mail as input, since there is a chance that the mandatee retrieved by e-mail
    # isn't the same one as the one already bound to the signing activity (minister vs MP, ...)
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

DELETE {
    GRAPH $graph {
        ?signing_activity dossier:Activiteit.einddatum ?end_date .
    }
}
INSERT {
    GRAPH $graph {
        ?signing_activity dossier:Activiteit.einddatum $end_date .
    }
}
WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?signing_activity a sign:Handtekenactiviteit ;
            sign:ondertekenaar ?signer .
        $signer a mandaat:Mandataris .
        OPTIONAL {
            ?signing_activity dossier:Activiteit.einddatum ?end_date .
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        signflow=sparql_escape_uri(signflow_uri),
        signer=sparql_escape_uri(mandatee_uri),
        end_date=sparql_escape_datetime(end_date)
    )
