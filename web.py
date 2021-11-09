from flask import g, request, make_response, redirect
from helpers import log, error, logger
from .authentication import signinghub_session_required, ensure_signinghub_machine_user_session
from .jsonapi import jsonapi_required
from .lib import uri, exceptions, get_signflow_pieces, prepare_signflow, generate_integration_url
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
            return error(f"Not Found: {exception.uri}", 404)

        data = [{
            "type": "pieces",
            "uri": p["uri"],
            "id": p["id"],
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
            return error(f"Not Found: {exception.uri}", 404)
        except exceptions.InvalidStateException as exception:
            return error(f"Invalid State: {exception}", 400)
        return make_response("", 204)
    except BaseException as exception:
        logger.exception("Internal Server Error")
        return error("Internal Server Error", 500)

@app.route('/publication-flow/<pubf_id>/signing/files/<file_id>/signers', methods=['GET'])
def file_signers_get(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)["uri"]
    sig_prep_act = get_signing_prep_from_subcase_file(subcase_uri, file_uri)
    try:
        mandatees = get_signing_mandatees(sig_prep_act["uri"])
        mandatees_data = []
        for mandatee in mandatees:
            mandatees_data.append({
                "type": "mandatees",
                "id": mandatee["uuid"]
            })
        status_code = 200
    except NoQueryResultsException: # No mandatees available
        mandatees_data = []
        status_code = 404
    res = make_response({"data": mandatees_data}, status_code)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/publication-flow/<pubf_id>/signing/files/<file_id>/signers', methods=['POST'])
@signinghub_session_required # provides g.sh_session
@jsonapi_required
def file_signers_post(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)["uri"]
    body = request.get_json(force=True)
    mandatees = list(filter(lambda f: f["type"] == "mandatees", body["data"]))
    for mandatee in mandatees: # A separate first loop, to make sure given id's are valid
        mandatee["uri"] = get_mandatee_by_id(mandatee["id"])["uri"]
    for mandatee in mandatees:
        add_signing_activity(subcase_uri, file_uri, mandatee["uri"])
    res = make_response({"data": mandatees}, 202)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/publication-flow/<pubf_id>/signing/files/<file_id>/start', methods=['POST'])
def start_signing(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)["uri"]
    signing_prep = get_signing_prep_from_subcase_file(subcase_uri, file_uri)
    g.sh_session.share_document_package(signing_prep["sh_package_id"])
    update_activities_signing_started(signing_prep["uri"])


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

