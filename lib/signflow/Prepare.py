from string import Template
from helpers import generate_uuid
from escape_helpers import sparql_escape_uri, sparql_escape_string
from .. import exceptions, sparql
from . import uri, GetPieces

def execute(signflow_uri):
    query_command = 

    if pieces is None:
        raise exceptions.ResourceNotFoundException(signflow_uri)

    if len(pieces) == 0:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no related pieces.")

    if len(pieces) != 1:
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has multiple pieces.")

    status = pieces[0]["status"]
    if status != "marked":
        raise exceptions.InvalidStateException(f"Signflow {signflow_uri} has no unprepared piece.")

    piece_uri = pieces[0]["uri"]

    preparation_activity_id = generate_uuid()
    preparation_activity_uri = uri.resource.preparation_activity(preparation_activity_id)

    signinghub_package_id = generate_uuid()
    signinghub_document_id = generate_uuid()
    signinghub_document = uri.resource.signinghub_document(signinghub_package_id, signinghub_document_id)

    update_command = _update_template.safe_substitute(
        graph=sparql_escape_uri(uri.graph.sign),
        signflow=sparql_escape_uri(signflow_uri),
        preparation_activity=sparql_escape_uri(preparation_activity_uri),
        preparation_activity_id=sparql_escape_string(preparation_activity_id),
        piece=sparql_escape_uri(piece_uri),
        sh_document=sparql_escape_uri(signinghub_document),
        sh_document_id=sparql_escape_string(signinghub_document_id),
        sh_package_id=sparql_escape_string(signinghub_package_id),
    )
    sparql.update(update_command)

_query_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX nfo: <http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#>
PREFIX nie: <http://www.semanticdesktop.org/ontologies/2007/01/19/nie#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signflow ?marking_activity ?preparation_activity (?piece AS ?uri) (?piece_id AS ?id) ?path
WHERE {
    GRAPH <http://mu.semte.ch/graphs/organizations/kanselarij> {
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
                ?piece ext:file ?file .
                ?file a nfo:FileDataObject ;
                    ^nie:dataSource ?path .
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

    VALUES ?signflow { <http://themis.vlaanderen.be/id/handtekenaangelegenheid/6171355D614D6D0009000013> }
}
""")

_update_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        $preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
        $preparation_activity a sign:Voorbereidingsactiviteit ;
            mu:uuid $preparation_activity_id .
        $preparation_activity sign:voorbereidingGenereert $sh_document .
        $sh_document a sh:Document ;
            sh:packageId $sh_package_id ;
            sh:documentId $sh_document_id ;
            prov:hadPrimarySource $piece .
    }
} WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
    }
}
""")