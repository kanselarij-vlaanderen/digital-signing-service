from string import Template
from helpers import query
from .query_result_helpers import to_recs, ensure_1
from escape_helpers import sparql_escape_uri, sparql_escape_string

def get_by_uuid(uuid: str, rdf_type=None):
    query_template = Template("""
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>

SELECT DISTINCT (?record as ?uri) ?type
WHERE {
    ?record a ?type ;
        mu:uuid $uuid .
    $type_filter
}
LIMIT 1
""")
    query_string = query_template.substitute(
        uuid=sparql_escape_string(uuid),
        type_filter=f"FILTER(?type ={sparql_escape_uri(rdf_type)})" if rdf_type else ""
        )
    query_result = query(query_string)
    records = to_recs(query_result)
    record = ensure_1(records)
    return record["uri"]
