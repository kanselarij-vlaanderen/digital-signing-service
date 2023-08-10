from urllib.parse import urljoin

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import g, make_response, request
from helpers import error, log, logger, query

from lib.query_result_helpers import to_recs

from . import jsonapi
from .agent_query import query as agent_query
from .authentication import (MACHINE_ACCOUNTS,
                             open_new_signinghub_machine_user_session,
                             signinghub_session_required)
from .config import SIGNINGHUB_APP_DOMAIN, SYNC_CRON_PATTERN
from .lib import assign_signers, exceptions, prepare_signing_flow, signing_flow
from .lib.generic import get_by_uuid
from .lib.update_signing_flow import update_signing_flow
from .queries.signing_flow import construct_get_signing_flows_by_uuids


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
    response_code = 200
    for ovo_code in MACHINE_ACCOUNTS.keys():
        try:
            sh_session = open_new_signinghub_machine_user_session(ovo_code)
            logger.info(f"Successful login for machine user account of {ovo_code} ({MACHINE_ACCOUNTS[ovo_code]['USERNAME']})")
            # sh_session.logout() doesn't work. https://manuals.ascertia.com/SigningHub/8.2/Api/#tag/Authentication/operation/V4_Account_LogoutUser specifies a (required?) device token which we don't have
        except Exception as e:
            response_code = 500
            logger.warn(f"Failed login for machine user account of {ovo_code} ({MACHINE_ACCOUNTS[ovo_code]['USERNAME']})")
            logger.warn(e)
    return make_response("", response_code)


@app.route('/signing-flows/upload-to-signinghub', methods=['POST'])
@jsonapi.header_required
@signinghub_session_required  # provides g.sh_session
def prepare_post():
    body = request.get_json(force=True)

    sign_flow_ids = [entry["id"] for entry in body["data"]]

    query_string = construct_get_signing_flows_by_uuids(sign_flow_ids)
    sign_flows = to_recs(query(query_string))

    prepare_signing_flow.prepare_signing_flow(g.sh_session, sign_flows)

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
