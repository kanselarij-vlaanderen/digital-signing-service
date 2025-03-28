from urllib.parse import urljoin
import traceback

import requests
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import make_response, request, jsonify
from helpers import error, logger, query, validate_json_api_content_type, update

from lib.query_result_helpers import to_recs

from .agent_query import query as agent_query
from .sudo_query import update as sudo_update
from .authentication import (MACHINE_ACCOUNTS,
                             open_new_signinghub_machine_user_session)
from .config import SIGNINGHUB_APP_DOMAIN, SYNC_CRON_PATTERN
from .lib import exceptions, signing_flow
from .lib.generic import get_by_uuid
from .lib.update_signing_flow import update_signing_flow
from .lib.mark_pieces_for_signing import mark_pieces_for_signing as mark_pieces_for_signing_impl
from .lib.file import delete_physical_file
from .lib.job import create_job, execute_job, get_job
from .queries.signing_flow import get_physical_files_of_sign_flows_by_id, remove_signflows
from .queries.file import delete_physical_file_metadata
from .queries.session import construct_delete_signinghub_sessions


def sync_all_ongoing_flows():
    records = signing_flow.get_ongoing_signing_flows(agent_query)
    logger.info(f"Starting synchronisation for {len(records)} signflows...")
    ids = list(map(lambda r: r["sign_flow_id"], records))
    for id in ids:
        requests.post(f"http://localhost/signing-flows/{id}/sync")
    logger.info("Synchronisation finished")

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
            logger.debug(f"Successful login for machine user account of {ovo_code} ({MACHINE_ACCOUNTS[ovo_code]['USERNAME']})")
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


# Service endpoint, should only be accessed from the service container
# In a hostend environment, execute the following command to fire this endpoint:
# > drc exec digital-signing curl -XDELETE http://localhost/sessions
# This endpoint should not be made available via the dispatcher, as it doesn't check the current session's rights
@app.route('/sessions', methods=['DELETE'])
def delete_sessions():
    delete_sessions_query = construct_delete_signinghub_sessions()
    sudo_update(delete_sessions_query)
    return make_response("", 204)


@app.route('/job/<job_id>')
def job(job_id):
    job = get_job(job_id)

    if job:
        del job["mu_session_uri"]
        res = jsonify(job)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    else:
        return error(f"Job not found", 404)


@app.route('/signing-flows/upload-to-signinghub', methods=['POST'])
def prepare_post():
    validate_json_api_content_type(request)
    body = request.get_json(force=True)

    sign_flow_uris = [entry["uri"] for entry in body["data"]]
    mu_session_id = request.headers["MU-SESSION-ID"]

    job = create_job(sign_flow_uris, mu_session_id)

    thread = threading.Thread(target=lambda: execute_job(job))
    thread.start()

    res = jsonify({
            "id": job["id"],
            "uri": job["uri"],
            "sign_flow_uris": job["sign_flow_uris"],
            "created": job["created"],
            "modified": job["modified"],
            "status": job["status"],
    })
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/signing-flows/<signflow_id>', methods=['DELETE'])
def signinghub_remove_signflow(signflow_id):
    physical_files = to_recs(query(get_physical_files_of_sign_flows_by_id([signflow_id])))
    update(remove_signflows([signflow_id]))
    for physical_file in physical_files:
        delete_physical_file(physical_file["uri"])
        update(delete_physical_file_metadata(physical_file["uri"]))
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
    new_status = update_signing_flow(signflow_uri)
    if new_status:
        logger.info(f"Status for signflow <{signflow_uri}> was changed to {new_status}")
    else:
        logger.info(f"Status for signflow <{signflow_uri}> was left unchanged")
    return make_response({}, 200)


@app.errorhandler(exceptions.ResourceNotFoundException)
def handle_resource_not_found(e):
    logger.exception(e.uri)
    return error(f"Not Found: {e.uri}", 404)


@app.errorhandler(exceptions.InvalidStateException)
def handle_invalid_state(e):
    logger.exception(f"Invalid State: {e}")
    return error(f"Invalid State: {e}", 400)
