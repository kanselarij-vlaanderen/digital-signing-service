import requests

from flask import g, request, make_response
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from helpers import log, error, logger, update

from .authentication import signinghub_session_required
from . import jsonapi
from .lib import exceptions, prepare_signing_flow, generate_integration_url, \
    signing_flow, assign_signers, start_signing_flow, mandatee
from .lib.generic import get_by_uuid
from .lib.update_signing_flow import update_signing_flow
from .queries.signing_flow_signers import construct_add_signer
from .agent_query import query as agent_query
from .config import SYNC_CRON_PATTERN

def sync_all_ongoing_flows():
    records = signing_flow.get_ongoing_signing_flows(agent_query)
    ids = list(map(lambda r: r["sign_flow_id"], records))
    for id in ids:
        requests.post(f"http://localhost/signing-flows/{id}/sync")

scheduler = BackgroundScheduler()
scheduler.add_job(sync_all_ongoing_flows, CronTrigger.from_crontab(SYNC_CRON_PATTERN))
scheduler.start()

@app.route("/signinghub-profile")
@signinghub_session_required  # provides g.sh_session
def sh_profile_info():
    """Maintenance endpoint for debugging SigningHub authentication"""
    return g.sh_session.get_general_profile_information()

@app.route('/signing-flows/<signflow_id>/pieces')
def pieces_get(signflow_id):
    signflow_uri = get_by_uuid(signflow_id)
    records = signing_flow.get_pieces(signflow_uri)

    data = [{
        "type": "pieces",
        "id": r["id"],
        "attributes": {
            "uri": r["uri"]
        }
    } for r in records]
    res = make_response({ "data": data }, 200)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res


@app.route('/signing-flows/<signflow_id>/upload-to-signinghub', methods=['POST'])
@jsonapi.header_required
@signinghub_session_required  # provides g.sh_session
def prepare_post(signflow_id):
    signflow_uri = get_by_uuid(signflow_id)
    pieces = signing_flow.get_pieces(signflow_uri)
    if any(piece["sh_document_id"] for piece in pieces):
        raise Exception("Signingflow has already been uploaded previously.")

    piece_uris = [piece["uri"] for piece in pieces]

    prepare_signing_flow.prepare_signing_flow(g.sh_session, signflow_uri, piece_uris)

    res = make_response("", 204)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res


# piece_id is a part of the URI for consistency with other URIs of this service
# SigningHubs API does not link signers to pieces
@app.route('/signing-flows/<signflow_id>/signers', methods=['GET', 'POST', 'DELETE'])
def signers(signflow_id):
    signflow_uri = get_by_uuid(signflow_id)
    signflow = signing_flow.get_signing_flow(signflow_uri)
    # if signflow["sh_package_id"]: # already on SH
        # ensure_signinghub_user_session()
    if request.method == 'GET':
        return signers_get(signflow_uri)
    elif request.method == 'POST':
        return signers_assign(signflow_uri)

def signers_get(signflow_uri):
    records = signing_flow.get_signers(signflow_uri)

    data = [{
        "type": "mandatees",
        "id": r["id"],
        "attributes": {
            "uri": r["uri"]
        }
    } for r in records]
    res = make_response({"data": data}, 200)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

# @jsonapi.header_required
def signers_assign(signflow_uri):
    try:
        body = request.get_json(force=True)
        data = body["data"]
        signers_identifications = [jsonapi.require_identification(r, "mandatees") for r in data]
    except:
        return error(f"Bad Request: invalid payload", 400)

    signer_ids = [r["id"] for r in signers_identifications]
    signer_uris = [get_by_uuid(id) for id in signer_ids]
    for signer_uri in signer_uris:
        update(construct_add_signer(signflow_uri, signer_uri))
    res = make_response({}, 204)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res


@app.route('/signing-flows/<signflow_id>/pieces/<piece_id>/signinghub-url')
@signinghub_session_required  # provides g.sh_session
def signinghub_integration_url(signflow_id, piece_id):
    signflow_uri = get_by_uuid(signflow_id)
    piece_uri = get_by_uuid(piece_id)
    collapse_panels = request.args.get(
        "collapse_panels", default="true", type=str) != "false"

    integration_url = generate_integration_url.generate_integration_url(
            g.sh_session, signflow_uri, piece_uri, collapse_panels)
    return make_response({"url": integration_url}, 200)


@app.route('/signing-flows/<signflow_id>/start', methods=['POST'])
@signinghub_session_required
def start(signflow_id):
    signflow_uri = get_by_uuid(signflow_id)

    start_signing_flow.start_signing_flow(g.sh_session, signflow_uri)

    res = make_response({}, 200)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res


# HTTP method not specified in api documentation
@app.route('/signinghub-callback', methods=['GET', 'POST'])
def signinghub_callback():
    data = request.get_json(force=True)
    sh_package_id = data["package_id"]
    action = data["action"]
    if action == "none":
        log("Someone looked at package_id '{}' through SigningHub Iframe")
    # elif action == "shared":  # Start signflow.
        # TODO
    # elif action in ("signed", "declined", "reviewed"):
        # TODO
    elif action == "forbidden":
        log("Someone tried to access forbidden package_id '{}' through SigningHub Iframe")
    return make_response("", 200)  # Because Flask expects a response

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
