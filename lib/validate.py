from string import Template
from helpers import query
from escape_helpers import sparql_escape_uri, sparql_escape_string
from . import query_result_helpers, exceptions
from ..config import KANSELARIJ_GRAPH

def ensure_mandatees_exist(mandatee_ids):
    exists_template = Template("""
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>

SELECT ?mandatee ?mandatee_id
WHERE {
    GRAPH $graph {
        ?mandatee a mandaat:Mandataris ;
            mu:uuid ?mandatee_id .
    }

    VALUES ?mandatee_id { $mandatee_ids }
}
""")
    uri_command = exists_template.substitute(
        graph=sparql_escape_uri(KANSELARIJ_GRAPH),
        mandatee_ids=query_result_helpers.sparql_escape_list([sparql_escape_string(id) for id in mandatee_ids]),
    )
    result = query(uri_command)
    mandatee_records = query_result_helpers.to_recs(result)
    mandatees_not_found = [r["mandatee_id"] for r in mandatee_records if not "mandatee" in mandatee_records]
    if not mandatees_not_found:
        raise exceptions.ResourceNotFoundException(','.join(mandatees_not_found))

    return [r["mandatee"] for r in mandatee_records]
