from urllib.parse import urljoin
import traceback

import requests
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import g, make_response, request, jsonify
from helpers import error, logger, query, validate_json_api_content_type, update

from lib.query_result_helpers import to_recs

from .agent_query import query as agent_query
from .authentication import (MACHINE_ACCOUNTS,
                             open_new_signinghub_machine_user_session,
                             signinghub_session_required)
from .config import SIGNINGHUB_APP_DOMAIN, SYNC_CRON_PATTERN
from .lib import exceptions, prepare_signing_flow, signing_flow
from .lib.generic import get_by_uuid
from .lib.update_signing_flow import update_signing_flow
from .lib.mark_pieces_for_signing import mark_pieces_for_signing as mark_pieces_for_signing_impl
from .lib.file import delete_physical_file
from .queries.signing_flow import construct_get_signing_flows_by_uuids, get_physical_files_of_sign_flows, remove_signflows, reset_signflows
from .queries.file import delete_physical_file_metadata


def sync_all_ongoing_flows():
    records = signing_flow.get_ongoing_signing_flows(agent_query)
    ids = list(map(lambda r: r["sign_flow_id"], records))
    for id in ids:
        requests.post(f"http://localhost/signing-flows/{id}/sync")

scheduler = BackgroundScheduler()
scheduler.add_job(sync_all_ongoing_flows, CronTrigger.from_crontab(SYNC_CRON_PATTERN))
scheduler.start()

@app.route("/verify-credentials")
def sh_profile_info():
    """Maintenance endpoint for debugging SigningHub authentication"""
    response_code = 204
    errors = []
    for ovo_code in MACHINE_ACCOUNTS.keys():
        try:
            open_new_signinghub_machine_user_session(ovo_code)
            logger.info(f"Successful login for machine user account of {ovo_code} ({MACHINE_ACCOUNTS[ovo_code]['USERNAME']})")
            # sh_session.logout() doesn't work. https://manuals.ascertia.com/SigningHub/8.2/Api/#tag/Authentication/operation/V4_Account_LogoutUser specifies a (required?) device token which we don't have
        except Exception as e:
            response_code = 500
            logger.warn(f"Failed login for machine user account of {ovo_code} ({MACHINE_ACCOUNTS[ovo_code].get('USERNAME')})")
            logger.exception(e)
            errors.append({
                "title": "Failed login for machine user account",
                "detail": traceback.format_exc(),
                "status": 500,
            })
    if response_code == 204:
        return make_response("", response_code)
    else:
        response = jsonify({
            "errors": errors,
        })
        response.status_code = 500
        response.headers["Content-Type"] = "application/vnd.api+json"
        return response


@app.route('/signing-flows/upload-to-signinghub', methods=['POST'])
@signinghub_session_required  # provides g.sh_session
def prepare_post():
    validate_json_api_content_type(request)
    body = request.get_json(force=True)

    sign_flow_ids = [entry["id"] for entry in body["data"]]

    query_string = construct_get_signing_flows_by_uuids(sign_flow_ids)
    sign_flows = to_recs(query(query_string))

    # Remove decision_report when it's equal to piece
    for sign_flow in sign_flows:
        if sign_flow["piece"] == sign_flow["decision_report"]:
            sign_flow["decision_report"] = None

    try:
        prepare_signing_flow.prepare_signing_flow(g.sh_session, sign_flows)
    except Exception as exception:
        physical_files = to_recs(query(get_physical_files_of_sign_flows(sign_flow_ids)))
        for physical_file in physical_files:
            delete_physical_file(physical_file["uri"])
            update(delete_physical_file_metadata(physical_file["uri"]))
        update(reset_signflows(sign_flow_ids))
        time.sleep(2)
        raise exception

    res = make_response("", 204)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/signing-flows/<signflow_id>', methods=['DELETE'])
def signinghub_remove_signflow(signflow_id):
    physical_files = to_recs(query(get_physical_files_of_sign_flows([signflow_id])))
    for physical_file in physical_files:
        delete_physical_file(physical_file["uri"])
        update(delete_physical_file_metadata(physical_file["uri"]))
    update(remove_signflows([signflow_id]))
    # Give cache time to update
    # Ideally we want to return the changed values so the frontend
    # can update without refetching the new data.
    time.sleep(2)
    return make_response("", 204)
    

@app.route('/signing-flows/mark-pieces-for-signing', methods=['POST'])
def mark_pieces_for_signing():
    body = request.get_json(force=True)

    piece_ids = [entry["id"] for entry in body["data"]]

    if len(piece_ids):
        mark_pieces_for_signing_impl(piece_ids)

    res = make_response("", 204)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res


@app.route('/signing-flows/<signflow_id>/pieces/<piece_id>/signinghub-url')
def signinghub_integration_url(signflow_id, piece_id):
    signflow_uri = get_by_uuid(signflow_id)
    signflow = signing_flow.get_signing_flow(signflow_uri)
    if signflow['sh_package_id']:
        url = urljoin(SIGNINGHUB_APP_DOMAIN, f"/Web#/Viewer/{signflow['sh_package_id']}/")
        return make_response({"url": url}, 200)
    return make_response("", 204)


# Service endpoint for manually initiating sync for a given signing flow
@app.route('/signing-flows/<signflow_id>/sync', methods=['POST'])
def signinghub_sync(signflow_id):
    signflow_uri = get_by_uuid(signflow_id, None, agent_query)
    update_signing_flow(signflow_uri)
    return make_response({}, 200)


@app.errorhandler(exceptions.ResourceNotFoundException)
def handle_resource_not_found(e):
    logger.exception(e.uri)
    return error(f"Not Found: {e.uri}", 404)


@app.errorhandler(exceptions.InvalidStateException)
def handle_invalid_state(e):
    logger.exception(f"Invalid State: {e}")
    return error(f"Invalid State: {e}", 400)
