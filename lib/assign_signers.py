import typing
from signinghub_api_client.client import SigningHubSession
from helpers import log, logger, generate_uuid, query, update
from escape_helpers import sparql_escape_uri, sparql_escape_string, sparql_escape_int, sparql_escape_datetime
from .helpers import sparql_escape_list
from . import exceptions, helpers, uri, validate
from .helpers import Template

def assign_signers(
    signinghub_session: SigningHubSession,
    signflow_uri: str, signer_uris: typing.List[str]):
    validate.ensure_signflow_exists(signflow_uri)
    #TODO: validation: ensure signflow is in draft
    mandatees_query_command = _query_mandatees_template.substitute(
        graph=sparql_escape_uri(uri.graph.application),
        mandatees=sparql_escape_list([sparql_escape_uri(uri) for uri in signer_uris]))
    mandatee_result = query(mandatees_query_command)
    mandatee_records = helpers.to_recs(mandatee_result)
    mandatee_records_set = { r["mandatee"] for r in mandatee_records }
    mandatees_not_found = [uri for uri in signer_uris if uri not in mandatee_records_set]
    if mandatees_not_found:
        raise exceptions.ResourceNotFoundException(','.join(mandatees_not_found))

    #TODO: validation: ensure signers are not assigned yet
    sh_document_query_command = _sh_documents_template.substitute(
        graph=sparql_escape_uri(uri.graph.application),
        signflow=sparql_escape_uri(signflow_uri),
    )
    sh_document_result = query(sh_document_query_command)
    sh_document_records = helpers.to_recs(sh_document_result)
    sh_document_record = helpers.ensure_1(sh_document_records)

    sh_package_id = sh_document_record["sh_package_id"]
    sh_users = [{
        "user_email": r["email"],
        "user_name": ' '.join([name for name in [r["first_name"], r["family_name"]] if name]),
        "role": "SIGNER"
    } for r in mandatee_records]
    signinghub_session.add_users_to_workflow(sh_package_id, sh_users)

    signing_activities = [_build_signing_activity(signer_uri) for signer_uri in signer_uris]

    signing_activities_escaped = helpers.sparql_escape_table([[
            sparql_escape_uri(r["uri"]),
            sparql_escape_string(r["id"]),
            sparql_escape_uri(r["mandatee_uri"])
    ] for r in signing_activities])

    assign_signers_command = _assign_signers_template.substitute(
        graph=sparql_escape_uri(uri.graph.kanselarij),
        signflow=sparql_escape_uri(signflow_uri),
        signing_activities=signing_activities_escaped)
    update(assign_signers_command)

    return signing_activities

def _build_signing_activity(mandatee_uri):
    signing_activity_id = generate_uuid()
    signing_activity_uri = uri.resource.signing_activity(signing_activity_id)

    return {
        "id": signing_activity_id,
        "uri": signing_activity_uri,
        "mandatee_uri": mandatee_uri
    }

_sh_documents_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

SELECT ?signflow ?piece ?sh_document ?sh_package_id ?sh_document_id
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        ?sign_subcase ^sign:voorbereidingVindtPlaatsTijdens ?preparation_activity .
        ?preparation_activity sign:voorbereidingGenereert ?sh_document .
        ?sh_document sh:packageId ?sh_package_id ;
            sh:documentId ?sh_document_id .
    }

    VALUES ?signflow { $signflow }
}
""")

# TODO: update to persoon:gebruikteVoornaam
_query_mandatees_template = Template("""
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>

SELECT ?mandatee ?email ?first_name ?family_name
WHERE {
    GRAPH $graph {
        ?mandatee a mandaat:Mandataris ;
            mandaat:isBestuurlijkeAliasVan ?person .
        OPTIONAL { ?person foaf:firstName ?first_name }
        OPTIONAL { ?person foaf:familyName ?family_name }
        OPTIONAL {
            ?person foaf:mbox ?email_uri .
            BIND( REPLACE(STR(?email_uri), "mailto:", "") AS ?email)
        }

        VALUES ?mandatee { $mandatees }
    }
}
""")

_assign_signers_template = Template("""
PREFIX mandaat: <http://data.vlaanderen.be/ns/mandaat#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dossier: <https://data.vlaanderen.be/ns/dossier#>
PREFIX mandaat: <https://data.vlaanderen.be/ns/mandaat#>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handteken/>
PREFIX signinghub: <http://mu.semte.ch/vocabularies/ext/signinghub/>


INSERT {
    GRAPH $graph {
        ?signing_activity a sign:Handtekenactiviteit ;
            mu:uuid ?signing_activity_id .
        ?signing_activity prov:wasInformedBy ?preparation_activity .
        ?signing_activity prov:qualifiedAssociation ?signer .
        ?signing_activity sign:handtekeningVindtPlaatsTijdens ?sign_subcase .
    }
}
WHERE {
    GRAPH $graph {
        ?signflow a sign:Handtekenaangelegenheid .
        ?signflow sign:doorlooptHandtekening ?sign_subcase .
        ?preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
    }

    VALUES ?signflow { $signflow }
    VALUES (?signing_activity ?signing_activity_id ?signer) { $signing_activities }
}
""")
