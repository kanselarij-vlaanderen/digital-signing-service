from datetime import datetime
from signinghub_api_client.client import SigningHubSession
from helpers import log, logger, generate_uuid, query, update
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime
from . import exceptions, helpers, uri, validate, __signflow_queries
from .helpers import Template

#TODO: validation
# - not started yet
# - assigned
def start_signflow(
    sh_session: SigningHubSession,
    signflow_uri: str):
    signflow = __signflow_queries.get_signflow(signflow_uri)
    sh_package_id = signflow["sh_package_id"]
    sh_session.share_document_package(sh_package_id)
    __register_start_signflow(signflow_uri)

def start_signflow_from_signinghub_callback(sh_package_id: str):
    signflow = __signflow_queries.get_signflow_by_signinghub_id(sh_package_id)
    signflow_uri = signflow["uri"]
    __register_start_signflow(signflow_uri)

def __register_start_signflow(signflow_uri: str):
    timestamp = datetime.now()
    update_activities_command = __update_activities_template.substitute(
        graph=sparql_escape_uri(uri.graph.kanselarij),
        signflow=sparql_escape_uri(signflow_uri),
        start_date=sparql_escape_datetime(timestamp)
    )
    update(update_activities_command)

__update_activities_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        ?preparation_activity dossier:Activiteit.einddatum ?start_date .
        ?signing_activity dossier:Activiteit.startdatum ?start_date .
    }
} WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid .
        ?signflow sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?sign_subcase ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .
        ?preparation_activity a sign:Voorbereidingsactiviteit .
        ?sign_subcase ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?signing_activity a sign:Handtekenactiviteit .
    }
    VALUES ?signflow { $signflow }
    VALUES ?start_date { $start_date }
}
""")