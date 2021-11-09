from datetime import datetime
from signinghub_api_client.client import SigningHubSession
from . import get_signflow_pieces
from helpers import log, logger, generate_uuid, query, update
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime
from . import exceptions, helpers, uri, validate
from .helpers import Template

#TODO: validation
# - not started yet
# - assigned
def start_signflow(
    sh_session: SigningHubSession,
    signflow_uri: str):
    sh_package_id_command = _sh_package_id_query_template.substitute(
        graph=sparql_escape_uri(uri.graph.application),
        signflow=sparql_escape_uri(signflow_uri),
    )
    result = query(sh_package_id_command)
    records = helpers.to_recs(result)
    record = helpers.ensure_1(records)
    sh_package_id = record["sh_package_id"]
    #sh_session.share_document_package(sh_package_id)
    update_activities_command = _update_activities_template.substitute(
        graph=sparql_escape_uri(uri.graph.kanselarij),
        start_date=sparql_escape_datetime(datetime.now()),
        signflow=sparql_escape_uri(signflow_uri)
    )
    logger.info(update_activities_command)
    update(update_activities_command)

_sh_package_id_query_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signflow ?sh_package_id ?sh_document_id
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid .
        ?signflow sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .

        ?preparation_activity a sign:Voorbereidingsactiviteit .
        ?preparation_activity sign:voorbereidingGenereert ?sh_document .
        ?sh_document a sh:Document .
        ?sh_document sh:packageId ?sh_package_id .
    }
    VALUES ?signflow { $signflow }
}
""")

_update_activities_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        ?preparation_activity dossier:einddatum ?start_date .
        ?signing_activity dossier:startdatum ?start_date .
    }
} WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid .
        ?signflow sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?sign_subcase sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .
        ?preparation_activity a sign:Voorbereidingsactiviteit .
        ?sign_subcase sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?signing_activity a sign:Handtekenactiviteit .
    }
    VALUES ?signflow { $signflow }
    VALUES ?start_date { $start_date }
}
""")