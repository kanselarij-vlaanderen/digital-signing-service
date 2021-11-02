from string import Template
from helpers import query
from escape_helpers import sparql_escape_string, sparql_escape_uri
from . import exceptions, helpers, uri, validate

def execute(signflow_uri: str):
    query_command = _query_template.safe_substitute({
        "graph": sparql_escape_uri(uri.graph.kanselarij),
        "signflow": sparql_escape_uri(signflow_uri)
    })
    results = query(query_command)
    records = helpers.to_recs(results)

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
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT DISTINCT ?signflow ?activity_type ?piece ?piece_id
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .

    	OPTIONAL { 
      		?piece a dossier:Stuk .
      		?piece mu:uuid ?piece_id .
    	}

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
            }
        }

        OPTIONAL {
      		?signing_activity sign:handtekeningVindtPlaatsTijdens ?sign_subcase .
      		?signing_activity a sign:Handtekenactiviteit .
      		OPTIONAL {
        		?signing_activity prov:wasInformedBy ?preparation_activity .
      		}
    	}

    	BIND (IF (BOUND (?signing_activity), sign:Handtekenactiviteit,
    		IF (BOUND (?preparation_activity), sign:Voorbereidingsactiviteit,
          		IF (BOUND (?marking_activity), sign:Markeringsactiviteit, ?NULL))) AS ?activity_type)
    }

    VALUES ?signflow { $signflow }
}
""")

def _get_status(record):
    switcher = {
        "http://mu.semte.ch/vocabularies/ext/handteken/Markeringsactiviteit": "marked",
        "http://mu.semte.ch/vocabularies/ext/handteken/Voorbereidingsactiviteit": "prepared",
        "http://mu.semte.ch/vocabularies/ext/handteken/Handtekenactiviteit": "open",
    }
    status = switcher.get(record["activity_type"])
    return status
