from string import Template
from datetime import datetime
from signinghub_api_client.client import SigningHubSession
from helpers import update
from escape_helpers import sparql_escape_uri, sparql_escape_datetime
from . import signing_flow
from ..config import APPLICATION_GRAPH

#TODO: validation
# - not started yet
# - assigned
def start_signing_flow(
    sh_session: SigningHubSession,
    signflow_uri: str):
    signflow = signing_flow.get_signing_flow(signflow_uri)
    sh_package_id = signflow["sh_package_id"]
    sh_session.share_document_package(sh_package_id)
    __register_start_signing_flow(signflow_uri)

def __register_start_signing_flow(signflow_uri: str):
    timestamp = datetime.now()
    update_activities_command = __update_activities_template.substitute(
        graph=sparql_escape_uri(APPLICATION_GRAPH),
        signflow=sparql_escape_uri(signflow_uri),
        start_date=sparql_escape_datetime(timestamp)
    )
    update(update_activities_command)

__update_activities_template = Template("""
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX ext: <http://mu.semte.ch/vocabularies/ext/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        ?preparation_activity dossier:Activiteit.einddatum ?start_date .
        ?signing_activity dossier:Activiteit.startdatum ?start_date .
    }
} WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap ;
            ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity ;
            ^sign:handtekeningVindtPlaatsTijdens ?signing_activity .
        ?preparation_activity a sign:Voorbereidingsactiviteit .
        ?signing_activity a sign:Handtekenactiviteit .
    }
    VALUES ?signflow { $signflow }
    VALUES ?start_date { $start_date }
}
""")