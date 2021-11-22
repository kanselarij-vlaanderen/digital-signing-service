from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime
from ..lib import uri
from ..lib.helpers import Template

def construct(signflow_uri: str):
    query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?piece ?piece_id ?sh_document_id
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase .
        ?marking_activity a sign:Markeringsactiviteit .
        ?marking_activity sign:gemarkeerdStuk ?piece .
        ?piece a dossier:Stuk ;
            mu:uuid ?piece_id .
    
        OPTIONAL {
            ?preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
            ?preparation_activity a sign:Voorbereidingsactiviteit .
            ?preparation_activity sign:voorbereidingGenereert ?signinghub_doc .
            ?signinghub_doc a signinghub:Document .
            ?signinghub_doc prov:hadPrimarySource ?piece .
            ?signinghub_doc signinghub:documentId ?sh_document_id .
        }
    
    }
            
    VALUES ?signflow { $signflow }
}
""")
    return query_template.substitute(
        graph=sparql_escape_uri(uri.graph.application),
        signflow= sparql_escape_uri(signflow_uri)
    )
