from string import Template

from escape_helpers import (sparql_escape_datetime, sparql_escape_string,
                            sparql_escape_uri)
from helpers import generate_uuid

from ..config import (APPLICATION_GRAPH,
                      GOEDKEURINGSACTIVITEIT_RESOURCE_BASE_URI,
                      WEIGERACTIVITEIT_RESOURCE_BASE_URI)


def construct(signflow_uri: str) -> str:
    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

SELECT DISTINCT ?approval_activity ?start_date ?end_date ?approver
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?sign_subcase .
    ?sign_subcase a sign:HandtekenProcedurestap ;
        ^sign:goedkeuringVindtPlaatsTijdens ?approval_activity .
    ?approval_activity a sign:Goedkeuringsactiviteit ;
        sign:goedkeurder ?approver .
    OPTIONAL {
        ?approval_activity dossier:Activiteit.startdatum ?start_date .
    }
    OPTIONAL {
        ?approval_activity dossier:Activiteit.einddatum ?end_date .
    }
}
""")
    return query_template.substitute(
        signflow=sparql_escape_uri(signflow_uri)
    )


def construct_update_approval_activity_start_date(signflow_uri: str, email, start_date, graph=APPLICATION_GRAPH) -> str:
    if not email.startswith("mailto:"):
        email = "mailto:" + email

    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

DELETE {
    GRAPH $graph {
        ?approval_activity dossier:Activiteit.startdatum ?start_date .
    }
}
INSERT {
    GRAPH $graph {
        ?approval_activity dossier:Activiteit.startdatum $start_date .
    }
}
WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:goedkeuringVindtPlaatsTijdens ?approval_activity .
        ?approval_activity a sign:Goedkeuringsactiviteit ;
            sign:goedkeurder $approver .
        OPTIONAL {
            ?approval_activity dossier:Activiteit.startdatum ?start_date .
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        signflow=sparql_escape_uri(signflow_uri),
        approver=sparql_escape_uri(email),
        start_date=sparql_escape_datetime(start_date)
    )


def construct_update_approval_activity_end_date(signflow_uri: str, email, end_date, graph=APPLICATION_GRAPH) -> str:
    if not email.startswith("mailto:"):
        email = "mailto:" + email

    query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

DELETE {
    GRAPH $graph {
        ?approval_activity dossier:Activiteit.einddatum ?end_date .
    }
}
INSERT {
    GRAPH $graph {
        ?approval_activity dossier:Activiteit.einddatum $end_date .
    }
}
WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:goedkeuringVindtPlaatsTijdens ?approval_activity .
        ?approval_activity a sign:Goedkeuringsactiviteit ;
            sign:goedkeurder $approver .
        OPTIONAL {
            ?approval_activity dossier:Activiteit.einddatum ?end_date .
        }
    }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(graph),
        signflow=sparql_escape_uri(signflow_uri),
        approver=sparql_escape_uri(email),
        end_date=sparql_escape_datetime(end_date)
    )

def construct_insert_approval_activity(signflow_uri: str, email) -> str:
    uuid = generate_uuid()
    uri = GOEDKEURINGSACTIVITEIT_RESOURCE_BASE_URI + uuid

    if not email.startswith("mailto:"):
        email = "mailto:" + email

    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>

INSERT {
    $approval_activity a sign:Goedkeuringsactiviteit ;
        mu:uuid $approval_id ;
        sign:goedkeuringVindtPlaatsTijdens ?sign_subcase ;
        sign:goedkeurder $approver .
}
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?sign_subcase .
    FILTER NOT EXISTS {
        ?existing_approval_activity a sign:Goedkeuringsactiviteit ;
            sign:goedkeuringVindtPlaatsTijdens ?sign_subcase ;
            sign:goedkeurder $approver .
    }
}
""")
    return query_template.substitute(
        approval_activity=sparql_escape_uri(uri),
        approval_id=sparql_escape_string(uuid),
        approver=sparql_escape_uri(email),
        signflow=sparql_escape_uri(signflow_uri)
    )

def construct_insert_approval_refusal_activity(signflow_uri: str, email, date) -> str:
    uuid = generate_uuid()
    uri = WEIGERACTIVITEIT_RESOURCE_BASE_URI + uuid

    if not email.startswith("mailto:"):
        email = "mailto:" + email

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
    ?approval_activity sign:goedkeuringIsGeweigerdDoor $refusal_activity .
}
WHERE {
    $signflow a sign:Handtekenaangelegenheid ;
        sign:doorlooptHandtekening ?sign_subcase .
    ?approval_activity a sign:Goedkeuringsactiviteit ;
        sign:goedkeuringVindtPlaatsTijdens ?sign_subcase ;
        sign:goedkeurder $approver .
    FILTER NOT EXISTS {
        ?existing_refusal_activity a sign:Weigeractiviteit ;
            sign:weigeringVindtPlaatsTijdens ?sign_subcase .
        ?approval_activity sign:goedkeuringIsGeweigerdDoor ?existing_refusal_activity .
    }
}
""")
    return query_template.substitute(
        refusal_activity=sparql_escape_uri(uri),
        refusal_activity_id=sparql_escape_string(uuid),
        approver=sparql_escape_uri(email),
        signflow=sparql_escape_uri(signflow_uri),
        date=sparql_escape_datetime(date)
    )
