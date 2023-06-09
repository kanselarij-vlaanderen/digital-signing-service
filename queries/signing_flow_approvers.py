from string import Template
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_datetime
from ..config import APPLICATION_GRAPH

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
