from string import Template
from escape_helpers import sparql_escape_string, sparql_escape_uri
from .. import exceptions, sparql
from . import uri

def execute(signflow_uri: str):
    query_command = _query_template.safe_substitute({
        "graph": sparql_escape_uri(uri.graph.sign),
        "signflow": sparql_escape_uri(signflow_uri)
    })
    
    results = sparql.query(query_command)
    records = sparql.to_recs(results)
    if len(records) == 0:
        return None

    has_piece = "id" in records[0]
    if not has_piece:
        return []

    records = [{
        "id": r["id"],
        "uri": r["uri"],
        "status": _get_status(r),
    } for r in records]

    return records

def _get_status(record):
    if "preparation_activity" in record:
        return "prepared"
    elif "marking_activity" in record:
        return "marked"
    else:
        raise Exception("status-unknown")

_query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signflow ?marking_activity ?preparation_activity (?piece AS ?uri) (?piece_id AS ?id)
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        OPTIONAL {
            ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase .
            ?marking_activity a sign:Markeringsactiviteit .
            OPTIONAL {
                ?marking_activity sign:gemarkeerdStuk ?piece .
                ?piece a dossier:Stuk ;
                    mu:uuid ?piece_id .
            }
        }
        OPTIONAL {
            ?preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
            ?preparation_activity a sign:Voorbereidingsactiviteit .
            OPTIONAL {
                ?preparation_activity sign:voorbereidingGenereert ?signinghub_doc .
                ?signinghub_doc a signinghub:Document ;
                prov:hadPrimarySource ?piece .
                    ?piece a dossier:Stuk ;
                    mu:uuid ?piece_id .

            }
        }
    }

    VALUES ?signflow { $signflow }
}
""")