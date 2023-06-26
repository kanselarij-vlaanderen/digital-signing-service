import itertools
from string import Template
from typing import Dict, List
from signinghub_api_client.client import SigningHubSession
from helpers import generate_uuid, update, logger
from escape_helpers import sparql_escape_uri, sparql_escape_string
from . import uri, signing_flow
from .mandatee import get_mandatee
from .document import upload_piece_to_sh
from ..config import APPLICATION_GRAPH

def group_by_decision_activity(sign_flows: List[Dict]):
    # TODO: Cope with the fact that at some point we need to support
    # optional decision activities
    get_decision_activity = lambda d: d["decision_activity"]
    return [list(g) for _, g in itertools.groupby(sign_flows, get_decision_activity)]

def prepare_signing_flow(sh_session: SigningHubSession, sign_flows: List[Dict]):
    """Prepares a signing flow in SigningHub based off multiple sign flows in Kaleidos."""
    for grouped_sign_flows in group_by_decision_activity(sign_flows):
        signinghub_package = sh_session.add_package({
            "workflow_mode": "ONLY_OTHERS" # OVRB staff who prepare the flows will never sign
        })
        package_id = signinghub_package["package_id"]

        sign_flow = grouped_sign_flows[0]["sign_flow"]
        decision_report = grouped_sign_flows[0]["decision_report"]
        if decision_report:
            upload_piece_to_sh(decision_report, package_id)

        sh_session.update_workflow_details(package_id, {"workflow_type": "CUSTOM"})

        # All sign flows we're treating *should* have the same
        # approvers/notification/signers, so it's okay to use the first
        # sign flow to get them.
        approvers = signing_flow.get_approvers(sign_flow)
        for approver in approvers:
            logger.info(f"adding approver {approver['email']} to flow")
            sh_session.add_users_to_workflow(package_id, [{
            "user_email": approver["email"],
            "user_name": approver["email"],
            "role": "REVIEWER",
            "email_notification": True,
            "signing_order": 1,
        }])

        notified = signing_flow.get_notified(sign_flow)
        for notify in notified:
            logger.info(f"adding notified {notify['email']} to flow")
            sh_session.add_users_to_workflow(package_id, [{
            "user_email": notify["email"],
            "user_name": notify["email"],
            "role": "CARBON_COPY",
            "email_notification": True,
            "signing_order": 1,
        }])

        signers = signing_flow.get_signers(sign_flow)
        for signer in signers:
            logger.info(f"adding signer {signer['uri']} to flow")
            signer = get_mandatee(signer["uri"])
            sh_session.add_users_to_workflow(package_id, [{
            "user_email": signer["email"],
            "user_name": f"{signer['first_name']} {signer['family_name']}",
            "role": "SIGNER",
            "email_notification": True,
            "signing_order": 2,
        }])

        for sign_flow in grouped_sign_flows:
            sign_flow_uri = sign_flow["sign_flow"]
            piece_uri = sign_flow["piece"]

            # Document
            signinghub_document_uri, _, _ = upload_piece_to_sh(piece_uri, package_id)

            preparation_activity_id = generate_uuid()
            preparation_activity_uri = uri.resource.preparation_activity(preparation_activity_id)

            query_string = _update_template.substitute(
                graph=sparql_escape_uri(APPLICATION_GRAPH),
                signflow=sparql_escape_uri(sign_flow_uri),
                preparation_activity=sparql_escape_uri(preparation_activity_uri),
                preparation_activity_id=sparql_escape_string(preparation_activity_id),
                sh_document=sparql_escape_uri(signinghub_document_uri),
            )
            update(query_string)

    return


# optional sign activities to link in case some were already created before sending to SH
_update_template = Template("""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX mu: <http://mu.semte.ch/vocabularies/core/>
PREFIX sign: <http://mu.semte.ch/vocabularies/ext/handtekenen/>
PREFIX sh: <http://mu.semte.ch/vocabularies/ext/signinghub/>

INSERT {
    GRAPH $graph {
        $preparation_activity sign:voorbereidingVindtPlaatsTijdens ?sign_subcase .
        $preparation_activity a sign:Voorbereidingsactiviteit ;
            mu:uuid $preparation_activity_id .
        $preparation_activity sign:voorbereidingGenereert $sh_document .
        ?signing_activity prov:wasInformedBy $preparation_activity .
        ?approval_activity sign:isGoedgekeurdDoor $preparation_activity .
        $preparation_activity sign:isGemarkeerdDoor ?marking_activity .
    }
} WHERE {
    GRAPH $graph {
        $signflow a sign:Handtekenaangelegenheid ;
            sign:doorlooptHandtekening ?sign_subcase .
        ?sign_subcase a sign:HandtekenProcedurestap .
        OPTIONAL {
            ?marking_activity sign:markeringVindtPlaatsTijdens ?sign_subcase .
        }
        OPTIONAL {
            ?signing_activity sign:handtekeningVindtPlaatsTijdens ?sign_subcase .
        }
        OPTIONAL {
            ?approval_activity sign:goedkeuringVindtPlaatsTijdens ?sign_subcase .
        }
    }
}
""")
