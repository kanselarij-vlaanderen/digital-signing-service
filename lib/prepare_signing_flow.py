import functools
from itertools import groupby
from datetime import datetime
from string import Template
from typing import Dict, List, Callable

from escape_helpers import sparql_escape_string, sparql_escape_uri
from helpers import generate_uuid, logger, query, update
from signinghub_api_client.client import SigningHubSession

from ..config import APPLICATION_GRAPH, ADD_SIGNATURE_FIELD_ENABLED, SIGNATURE_FIELD_WIDTH, SIGNATURE_FIELD_HEIGHT
from ..utils import pythonize_iso_timestamp
from . import signing_flow, uri
from .document import upload_piece_to_sh
from .kaleidos_document_name import DOC_NAME_REGEX, compare_piece_names
from .mandatee import get_mandatee
from ..constants import DECISION_REPORT_TYPE_URI


def sort_sign_flows_by_piece(sign_flows: List[Dict]):
    def compare_valid_sign_flows(sign_flow1, sign_flow2) -> int:
        name1 = sign_flow1["piece_name"]
        name2 = sign_flow2["piece_name"]

        return compare_piece_names(name1, name2)

    def compare_invalid_sign_flows(sign_flow1, sign_flow2) -> int:
        created1 = datetime.fromisoformat(pythonize_iso_timestamp(sign_flow1["piece_created"]))
        created2 = datetime.fromisoformat(pythonize_iso_timestamp(sign_flow2["piece_created"]))

        if created1 and created2:
            return int(created2.timestamp()) - int(created1.timestamp())
        else:
            return 0

    valid_names = []
    invalid_names = []
    for sign_flow in sign_flows:
        piece_name = sign_flow["piece_name"]
        match = DOC_NAME_REGEX.match(piece_name) if piece_name else None
        if match:
            valid_names.append(sign_flow)
        else:
            invalid_names.append(sign_flow)

    return (sorted(valid_names, key=functools.cmp_to_key(compare_valid_sign_flows)) +
            sorted(invalid_names, key=functools.cmp_to_key(compare_invalid_sign_flows)))


def group_by_meeting_or_decision_activity(sign_flows: List[Dict]):
    get_meeting = lambda d: d.get("meeting", "")
    get_decision_activity = lambda d: d.get("decision_activity", "")

    grouped_flows = []

    grouped_by_meeting = [
        (meeting, list(group))
        for meeting, group in groupby(sorted(sign_flows, key=get_meeting), get_meeting)
    ]

    for meeting, group in grouped_by_meeting:
        if meeting != "":
            grouped_flows.append(group)
        else:
            grouped_flows.extend(
                [
                    list(g)
                    for _, g in groupby(
                        sorted(group, key=get_decision_activity), get_decision_activity
                    )
                ]
            )

    return grouped_flows


def prepare_signing_flow(
    sh_session: SigningHubSession,
    sign_flows: List[Dict],
    query_method: Callable = query,
    update_method: Callable = update,
):
    """Prepares a signing flow in SigningHub based off multiple sign flows in Kaleidos."""
    for grouped_sign_flows in group_by_meeting_or_decision_activity(sign_flows):
        signinghub_package = sh_session.add_package({
            "workflow_mode": "ONLY_OTHERS" # OVRB staff who prepare the flows will never sign
        })
        package_id = signinghub_package["package_id"]

        sign_flow = grouped_sign_flows[0]["sign_flow"]
        decision_report = grouped_sign_flows[0]["decision_report"]
        if decision_report:
            upload_piece_to_sh(sh_session, decision_report, package_id)

        sh_session.update_workflow_details(package_id, {"workflow_type": "CUSTOM"})

        # All sign flows we're treating *should* have the same
        # approvers/notification/signers, so it's okay to use the first
        # sign flow to get them.
        approvers = signing_flow.get_approvers(sign_flow, query_method)
        for approver in approvers:
            logger.info(f"adding approver {approver['email']} to flow")
            sh_session.add_users_to_workflow(package_id, [{
            "user_email": approver["email"],
            "user_name": approver["email"],
            "role": "REVIEWER",
            "email_notification": True,
            "signing_order": 1,
        }])

        notified = signing_flow.get_notified(sign_flow, query_method)
        for notify in notified:
            logger.info(f"adding notified {notify['email']} to flow")
            sh_session.add_users_to_workflow(package_id, [{
            "user_email": notify["email"],
            "user_name": notify["email"],
            "role": "CARBON_COPY",
            "email_notification": True,
            "signing_order": 1,
        }])

        signers = signing_flow.get_signers(sign_flow, query_method)
        signer_mandatees = []
        for signer in signers:
            logger.info(f"adding signer {signer['uri']} to flow")
            signer = get_mandatee(signer["uri"], query_method)
            signer_mandatees.append(signer)
            sh_session.add_users_to_workflow(package_id, [{
                "user_email": signer["email"],
                "user_name": f"{signer['first_name']} {signer['family_name']}",
                "role": "SIGNER",
                "email_notification": True,
                "signing_order": 2,
            }])

        for sign_flow in sort_sign_flows_by_piece(grouped_sign_flows):
            sign_flow_uri = sign_flow["sign_flow"]
            piece_uri = sign_flow["piece"]

            # Document
            signinghub_document_uri, _, signinghub_document_id = upload_piece_to_sh(piece_uri, package_id)

            # Auto-place signature field
            if ADD_SIGNATURE_FIELD_ENABLED:
                if sign_flow["piece_type"] == DECISION_REPORT_TYPE_URI:
                    logger.info(f"auto-placing signature field for {piece_uri} {package_id} {signinghub_document_id}")
                    for mandatee in signer_mandatees:
                        logger.info(f"placing field for signer {mandatee}")
                        try:
                            sh_session.auto_place_signature_field(package_id, signinghub_document_id, {
                                "search_text": f"{mandatee['first_name']} {mandatee['family_name']}",
                                "order": 1,
                                "field_type": "SIGNATURE",
                                "level_of_assurance": ["QUALIFIED_ELECTRONIC_SIGNATURE"],
                                "placement": "TOP",
                                "max_length": 9999,
                                "dimensions": { "width": SIGNATURE_FIELD_WIDTH, "height": SIGNATURE_FIELD_HEIGHT },
                                "multiline": True
                            })
                        except Exception as e:
                            logger.warn("Something went wrong while auto-placing sign field")
                            logger.exception(e)

            preparation_activity_id = generate_uuid()
            preparation_activity_uri = uri.resource.preparation_activity(preparation_activity_id)

            query_string = _update_template.substitute(
                graph=sparql_escape_uri(APPLICATION_GRAPH),
                signflow=sparql_escape_uri(sign_flow_uri),
                preparation_activity=sparql_escape_uri(preparation_activity_uri),
                preparation_activity_id=sparql_escape_string(preparation_activity_id),
                sh_document=sparql_escape_uri(signinghub_document_uri),
            )
            update_method(query_string)

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
