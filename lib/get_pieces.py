from string import Template
from helpers import query
from escape_helpers import sparql_escape_string, sparql_escape_uri
from . import exceptions, sparql, uri

def execute(signflow_uri: str):
    query_command = _query_template.safe_substitute({
        "graph": sparql_escape_uri(uri.graph.sign),
        "signflow": sparql_escape_uri(signflow_uri)
    })
    results = query(query_command)
    records = sparql.to_recs(results)

    if not records:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    has_piece = "piece_id" in records[0]
    if not has_piece:
        return []

    records = [{
        "id": r["piece_id"],
        "uri": r["piece"],
        "status": _get_status(r),
    } for r in records]

    return records

_query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX nie: <http://www.semanticdesktop.org/ontologies/2007/01/19/nie#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signflow ?marking_activity ?preparation_activity ?piece ?piece_id
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

def _get_status(record):
    if "preparation_activity" in record:
        return "prepared"
    elif "marking_activity" in record:
        return "marked"
    else:
        raise Exception("status-unknown")
