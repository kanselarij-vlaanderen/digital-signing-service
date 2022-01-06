from flask import g, json, request, make_response, redirect
from helpers import log, error, logger
from .authentication import signinghub_session_required, ensure_signinghub_machine_user_session
from . import jsonapi
from .lib import exceptions, prepare_signing_flow, generate_integration_url, \
    signing_flow, assign_signers, start_signing_flow, mandatee
from .lib.document import get_document_by_uuid

@app.route("/signinghub-profile")
@signinghub_session_required  # provides g.sh_session
def sh_profile_info():
    """Maintenance endpoint for debugging SigningHub authentication"""
    return g.sh_session.get_general_profile_information()


@app.route('/sign-flows/<signflow_id>/signing/pieces', methods=['GET'])
def pieces_get(signflow_id):
    signflow_uri = signing_flow.get_signing_flow_by_uuid(signflow_id)
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


@app.route('/signing-flows/<signflow_id>/upload-document-to-signinghub', methods=['POST'])
@jsonapi.header_required
@signinghub_session_required  # provides g.sh_session
def prepare_post(signflow_id):
    signflow_uri = signing_flow.get_signing_flow_by_uuid(signflow_id)
    try:
        body = request.get_json(force=True)
        data = body["data"]
        piece_identifations = [jsonapi.require_identification(r, "pieces") for r in data]
    except:
        return error(f"Bad Request: invalid payload", 400)

    piece_ids = [r["id"] for r in piece_identifations]
    piece_uris = [get_document_by_uuid(id) for id in piece_ids]

    prepare_signing_flow.prepare_signing_flow(g.sh_session, signflow_uri, piece_uris)

    res = make_response("", 204)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res


# piece_id is a part of the URI for consistency with other URIs of this service
# SigningHubs API does not link signers to pieces
@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signers', methods=['GET'])
def signers_get(signflow_id, piece_id):
    signflow_uri = signing_flow.get_signing_flow_by_uuid(signflow_id)
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


# piece_id is a part of the URI for consistency with other URIs of this service
# SigningHubs API does not link signers to pieces
@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signers', methods=['POST'])
@jsonapi.header_required
@signinghub_session_required  # provides g.sh_session
def signers_assign(signflow_id, piece_id):
    signflow_uri = signing_flow.get_signing_flow_by_uuid(signflow_id)
    try:
        body = request.get_json(force=True)
        data = body["data"]
        signers_identifications = [jsonapi.require_identification(r, "mandatees") for r in data]
    except:
        return error(f"Bad Request: invalid payload", 400)

    signer_ids = [r["id"] for r in signers_identifications]
    signer_uris = [mandatee.get_mandatee_by_id(id) for id in signer_ids]
    assign_signers.assign_signers(
        g.sh_session, signflow_uri, signer_uris)

    res = make_response({}, 204)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res


@app.route('/signing-flows/<signflow_id>/pieces/<piece_id>/signinghub-url', methods=['GET'])
@signinghub_session_required  # provides g.sh_session
def signinghub_integration_url(signflow_id, piece_id):
    signflow_uri = signing_flow.get_signing_flow_by_uuid(signflow_id)
    piece_uri = get_document_by_uuid(piece_id)
    collapse_panels = request.args.get(
        "collapse_panels", default="true", type=str) != "false"

    integration_url = generate_integration_url.generate_integration_url(
            g.sh_session, signflow_uri, piece_uri, collapse_panels)
    return make_response({"url": integration_url}, 200)


@signinghub_session_required
@app.route('/signing-flows/<signflow_id>/start', methods=['POST'])
def start(signflow_id):
    signflow_uri = signing_flow.get_signing_flow_by_uuid(signflow_id)

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

@app.errorhandler(exceptions.ResourceNotFoundException)
def handle_resource_not_found(e):
    logger.exception(e.uri)
    return error(f"Not Found: {e.uri}", 404)

@app.errorhandler(exceptions.InvalidStateException)
def handle_invalid_state(e):
    logger.exception(f"Invalid State: {e}")
    return error(f"Invalid State: {e}", 400)
