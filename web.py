from flask import g, json, request, make_response, redirect
from helpers import log, error, logger
from .authentication import signinghub_session_required, ensure_signinghub_machine_user_session
from . import jsonapi
from .lib import uri, exceptions, validate, \
    get_signflow_pieces, prepare_signflow, generate_integration_url, \
    signflow, get_signflow_signers, assign_signers, start_signflow
from .lib.activity import update_signing_status, \
    wrap_up_signing_flow

@app.route("/signinghub-profile")
@signinghub_session_required  # provides g.sh_session
def sh_profile_info():
    """Maintenance endpoint for debugging SigningHub authentication"""
    return g.sh_session.get_general_profile_information()


@app.route('/sign-flows/<signflow_id>/signing/pieces', methods=['GET'])
def pieces_get(signflow_id):
    try:
        signflow_uri = signflow.get_signflow_by_uuid(signflow_id)
        try:
            pieces = get_signflow_pieces.get_signflow_pieces(signflow_uri)
        except exceptions.ResourceNotFoundException as exception:
            logger.exception(f"Not found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)

        data = [{
            "type": "pieces",
            "id": p["id"],
        } for p in pieces]
        res = make_response({ "data": data }, 200)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)

@app.route('/sign-flows/<signflow_id>/signing/prepare', methods=['POST'])
@jsonapi.header_required
@signinghub_session_required  # provides g.sh_session
def prepare_post(signflow_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        try:
            body = request.get_json(force=True)
            data = body["data"]
            piece_identifations = [jsonapi.require_identification(r, "pieces") for r in data]
        except:
            return error(f"Bad Request: invalid payload", 400)

        piece_ids = [r["id"] for r in piece_identifations]
        piece_uris = [uri.resource.piece(id) for id in piece_ids]

        try:
            prepare_signflow.prepare_signflow(
                g.sh_session, signflow_uri, piece_uris)
        except exceptions.ResourceNotFoundException as exception:
            logger.exception(f"Not Found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.exception(f"Invalid State: {str(exception)}")
            return error(f"Invalid State: {exception}", 400)

        res = make_response("", 204)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)


# piece_id is a part of the URI for consistency with other URIs of this service
# SigningHubs API does not link signers to pieces
@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signers', methods=['GET'])
def signers_get(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        try:
            signers = get_signflow_signers.get_signflow_signers(signflow_uri)
        except exceptions.ResourceNotFoundException as exception:
            logger.exception(f"Not Found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.exception(f"Invalid State: {str(exception)}")
            return error(f"Invalid State: {exception}", 400)

        data = [{
            "type": "mandatees",
            "id": r["id"],
        } for r in signers]
        res = make_response({"data": data}, 200)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)


# piece_id is a part of the URI for consistency with other URIs of this service
# SigningHubs API does not link signers to pieces
@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signers', methods=['POST'])
@jsonapi.header_required
@signinghub_session_required  # provides g.sh_session
def signers_assign(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        try:
            body = request.get_json(force=True)
            data = body["data"]
            signers_identifications = [jsonapi.require_identification(r, "mandatees") for r in data]
        except:
            return error(f"Bad Request: invalid payload", 400)

        signer_ids = [r["id"] for r in signers_identifications]
        try:
            signer_uris = validate.ensure_mandatees_exist(signer_ids)
            assign_signers.assign_signers(
                g.sh_session, signflow_uri, signer_uris)
        except exceptions.ResourceNotFoundException as exception:
            logger.exception(f"Not Found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.exception(f"Invalid State: {str(exception)}")
            return error(f"Invalid State: {exception}", 400)
        
        res = make_response({}, 204)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)


@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signinghub-url', methods=['GET'])
@signinghub_session_required  # provides g.sh_session
def signinghub_integration_url(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        piece_uri = uri.resource.piece(piece_id)
        collapse_panels = request.args.get(
            "collapse_panels", default="true", type=str) != "false"
        try:
            integration_url = generate_integration_url.generate_integration_url(
                g.sh_session, signflow_uri, piece_uri, collapse_panels)
        except exceptions.ResourceNotFoundException as exception:
            logger.exception(f"Not found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.exception(f"Invalid state: {exception}")
            return error(f"Invalid State: {exception}", 400)
        return make_response({"url": integration_url}, 200)
    except BaseException as exception:
        logger.exception("Internal server error")
        return error("Internal Server Error", 500)


@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/start', methods=['POST'])
@jsonapi.header_required
@signinghub_session_required
def start(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        try:
            start_signflow.start_signflow(g.sh_session, signflow_uri)
        except exceptions.ResourceNotFoundException as exception:
            logger.exception(exception.uri)
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.exception(f"Invalid State: {exception}")
            return error(f"Invalid State: {exception}", 400)
        res = make_response({}, 200)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    except BaseException as exception:
        logger.exception("Internal server error")
        return error("Internal Server Error", 500)


# HTTP method not specified in api documentation
@app.route('/signinghub-callback', methods=['GET', 'POST'])
def signinghub_callback():
    data = request.get_json(force=True)
    sh_package_id = data["package_id"]
    action = data["action"]
    if action == "none":
        log("Someone looked at package_id '{}' through SigningHub Iframe")
    elif action == "shared":  # Start signflow.
        ensure_signinghub_machine_user_session()  # provides g.sh_session
        start_signflow.start_signflow_from_signinghub_callback(sh_package_id)
    elif action in ("signed", "declined", "reviewed"):
        # TODO: align with new data model
        ensure_signinghub_machine_user_session()  # provides g.sh_session
        update_signing_status(sh_package_id)
        # Attempt to wrap up in case this was the last signature required
        wrap_up_signing_flow(sh_package_id)
    elif action == "forbidden":
        log("Someone tried to access forbidden package_id '{}' through SigningHub Iframe")
    return make_response("", 200)  # Because Flask expects a response
