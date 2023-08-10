from string import Template

from escape_helpers import (sparql_escape_datetime, sparql_escape_string,
                            sparql_escape_uri)
from helpers import generate_uuid

from ..config import APPLICATION_GRAPH, WEIGERACTIVITEIT_RESOURCE_BASE_URI

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


def construct_update_signing_activity_start_date(signflow_uri: str, mandatee_uri, start_date, graph=APPLICATION_GRAPH) -> str:
    # TODO: probably needs e-mail as input, since there is a chance that the mandatee retrieved by e-mail
    # isn't the same one as the one already bound to the signing activity (minister vs MP, ...)
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

DELETE {
    GRAPH $graph {
        ?signing_activity dossier:Activiteit.startdatum ?start_date .
    }
}
INSERT {
    GRAPH $graph {
        ?signing_activity dossier:Activiteit.startdatum $start_date .
    }
}
WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?signing_activity a sign:Handtekenactiviteit ;
            sign:ondertekenaar $signer .
        OPTIONAL {
            ?signing_activity dossier:Activiteit.startdatum ?start_date .
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        signflow=sparql_escape_uri(signflow_uri),
        signer=sparql_escape_uri(mandatee_uri),
        start_date=sparql_escape_datetime(start_date)
    )


def construct_update_signing_activity_end_date(signflow_uri: str, mandatee_uri, end_date, graph=APPLICATION_GRAPH) -> str:
    # TODO: probably needs e-mail as input, since there is a chance that the mandatee retrieved by e-mail
    # isn't the same one as the one already bound to the signing activity (minister vs MP, ...)
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
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
            sign:ondertekenaar $signer .
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


def construct_insert_signing_refusal_activity(signflow_uri: str, mandatee_uri, date) -> str:
    uuid = generate_uuid()
    uri = WEIGERACTIVITEIT_RESOURCE_BASE_URI + uuid

    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>

INSERT {
    $refusal_activity a sign:Weigeractiviteit ;
        mu:uuid $refusal_activity_id ;
        sign:weigeringVindtPlaatsTijdens ?sign_subcase ;
        dossier:Activiteit.startdatum $date ;
        dossier:Activiteit.einddatum $date .
    ?signing_activity sign:isGeweigerdDoor $refusal_activity .
}
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?sign_subcase .
    ?signing_activity a sign:Handtekenactiviteit ;
        sign:handtekeningVindtPlaatsTijdens ?sign_subcase ;
        sign:ondertekenaar $signer .
    FILTER NOT EXISTS {
        ?existing_refusal_activity a sign:Weigeractiviteit ;
            sign:weigeringVindtPlaatsTijdens ?sign_subcase .
        ?signing_activity sign:isGeweigerdDoor ?existing_refusal_activity .
    }
}
""")
    return query_template.substitute(
        refusal_activity=sparql_escape_uri(uri),
        refusal_activity_id=sparql_escape_string(uuid),
        signer=sparql_escape_uri(mandatee_uri),
        signflow=sparql_escape_uri(signflow_uri),
        date=sparql_escape_datetime(date)
    )
