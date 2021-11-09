from flask import g, request, make_response, redirect
from helpers import log, error, logger
from .authentication import signinghub_session_required, ensure_signinghub_machine_user_session
from .jsonapi import jsonapi_required
from .lib import uri, exceptions, \
    get_signflow_pieces, prepare_signflow, generate_integration_url, \
    get_signers, assign_signers, start_signflow
from .lib.pub_flow import get_subcase_from_pub_flow_id
from .lib.activity import get_signing_prep_from_subcase_file, \
    get_signing_prep_from_sh_package_id, \
    add_signing_activity, \
    update_activities_signing_started, \
    update_signing_status, \
    wrap_up_signing_flow
from .lib.file import get_file_by_id
from .lib.mandatee import get_mandatee_by_id, get_signing_mandatees
from .lib.exceptions import NoQueryResultsException

@app.route("/signinghub-profile")
@signinghub_session_required # provides g.sh_session
def sh_profile_info():
    """Maintenance endpoint for debugging SigningHub authentication"""
    return g.sh_session.get_general_profile_information()

@app.route('/sign-flows/<signflow_id>/signing/pieces', methods=['GET'])
def pieces_get(signflow_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        try:
            pieces = get_signflow_pieces.get_signflow_pieces(signflow_uri)
        except exceptions.ResourceNotFoundException as exception:
            logger.info(f"Not found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)

        data = [{
            "type": "pieces",
            "uri": p["uri"],
            "id": p["id"],
            "status": p["status"]
        } for p in pieces]
        res = make_response({ "data": data }, 200)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)

@app.route('/sign-flows/<signflow_id>/signing/prepare', methods=['POST'])
@signinghub_session_required # provides g.sh_session
def prepare_post(signflow_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        body = request.get_json(force=True)
        data = body["data"]
        piece_uris = data["pieces"]
        try:
            prepare_signflow.prepare_signflow(g.sh_session, signflow_uri, piece_uris)
        except exceptions.ResourceNotFoundException as exception:
            logger.info(f"Not Found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.info(f"Invalid State: {str(exception)}")
            return error(f"Invalid State: {exception}", 400)

        return make_response("", 204)
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)

@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signers', methods=['GET'])
def signers_get(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        piece_uri = uri.resource.piece(piece_id)
        try:
            signers = get_signers.get_signers(signflow_uri)
        except exceptions.ResourceNotFoundException as exception:
            logger.info(f"Not Found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.info(f"Invalid State: {str(exception)}")
            return error(f"Invalid State: {exception}", 400)

        res = make_response({"data": signers}, 200)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)

@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/assign', methods=['POST'])
@signinghub_session_required # provides g.sh_session
def signers_assign(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        piece_uri = uri.resource.piece(piece_id)
        try:
            body = request.get_json(force=True)
            signer_uris = body["data"]["signers"]
        except:
            return error(f"Bad Request: invalid payload", 400)

        try:
            signing_activities = assign_signers.assign_signers(g.sh_session, signflow_uri, signer_uris)
        except exceptions.ResourceNotFoundException as exception:
            logger.info(f"Not Found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.info(f"Invalid State: {str(exception)}")
            return error(f"Invalid State: {exception}", 400)

        body = { "data": { "signing-activities": signing_activities, } }
        res = make_response(body, 204)
        return res
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)

@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signinghub', methods=['GET'])
@signinghub_session_required # provides g.sh_session
def signinghub_integration(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        piece_uri = uri.resource.piece(piece_id)
        collapse_panels = request.args.get("collapse_panels", default="true", type=str) != "false"
        try:
            integration_url = generate_integration_url.generate_integration_url(g.sh_session, signflow_uri, piece_uri, collapse_panels)
        except exceptions.ResourceNotFoundException as exception:
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.exception(f"Invalid state: {exception}")
            return error(f"Invalid State: {exception}", 400)
        return redirect(integration_url, 303)
    except BaseException as exception:
        logger.exception("Internal server error")
        return error("Internal Server Error", 500)

@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/signinghub-url', methods=['GET'])
@signinghub_session_required # provides g.sh_session
def signinghub_integration_url(signflow_id, piece_id):
    try:
        signflow_uri = uri.resource.signflow(signflow_id)
        piece_uri = uri.resource.piece(piece_id)
        collapse_panels = request.args.get("collapse_panels", default="true", type=str) != "false"
        try:
            integration_url = generate_integration_url.generate_integration_url(g.sh_session, signflow_uri, piece_uri, collapse_panels)
        except exceptions.ResourceNotFoundException as exception:
            logger.exception(f"Not found: {exception.uri}")
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            logger.exception(f"Invalid state: {exception}")
            return error(f"Invalid State: {exception}", 400)
        print(integration_url)
        return make_response({ "url": integration_url }, 200)
    except BaseException as exception:
        logger.exception("Internal server error")
        return error("Internal Server Error", 500)

@app.route('/sign-flows/<signflow_id>/signing/pieces/<piece_id>/start', methods=['POST'])
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
        return make_response("", 200)
    except BaseException as exception:
        logger.exception("Internal server error")
        return error("Internal Server Error", 500)

@app.route('/signinghub-callback', methods=['GET, POST']) # HTTP method not specified in api documentation
def signinghub_callback():
    data = request.json()
    sh_package_id = data["package_id"]
    action = data["action"]
    if action == "none":
        log("Someone looked at package_id '{}' through SigningHub Iframe")
    elif action == "shared": # Start pubflow. Normally handled through API call wired to custom button.
        ensure_signinghub_machine_user_session() # provides g.sh_session
        sig_prep = get_signing_prep_from_sh_package_id(sh_package_id)
        update_activities_signing_started(sig_prep["uri"])
    elif action in ("signed", "declined", "reviewed"):
        ensure_signinghub_machine_user_session() # provides g.sh_session
        update_signing_status(sh_package_id)
        wrap_up_signing_flow(sh_package_id) # Attempt to wrap up in case this was the last signature required
    elif action == "forbidden":
        log("Someone tried to access forbidden package_id '{}' through SigningHub Iframe")

