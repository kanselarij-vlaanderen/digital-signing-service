from flask import g, request, make_response, redirect
from helpers import log
from .authentication import signinghub_machine_session_required, ensure_signinghub_machine_user_session
from .jsonapi import jsonapi_required
from .lib.pub_flow import get_subcase_from_pub_flow_id
from .lib.activity import get_signing_preps_from_subcase, \
    get_signing_prep_from_subcase_file, \
    get_signing_prep_from_sh_package_id, \
    create_signing_prep_activity, \
    add_signing_activity, \
    update_activities_signing_started, \
    update_signing_status, \
    wrap_up_signing_flow
from .lib.file import get_file_by_id
from .lib.mandatee import get_mandatee_by_id, get_signing_mandatees
from .lib.exceptions import NoQueryResultsException

import logging
logging.basicConfig(level=logging.DEBUG)

@app.route("/signinghub-profile")
@signinghub_machine_session_required # provides g.sh_session
def sh_profile_info():
    """Maintenance endpoint for debugging SigningHub authentication"""
    return g.sh_session.get_general_profile_information()

@app.route('/publication-flow/<pubf_id>/signing/files', methods=['GET'])
def pubflow_files_get(pubf_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    try:
        signing_preps = get_signing_preps_from_subcase(subcase_uri)
        files = []
        for signing_prep in signing_preps:
            files.append({
                "type": "files",
                "id": signing_prep["file_id"]
            })
        status_code = 200
    except NoQueryResultsException: # No signing preps available
        files = []
        status_code = 404
    res = make_response({"data": files}, status_code)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/publication-flow/<pubf_id>/signing/files', methods=['POST'])
@signinghub_machine_session_required # provides g.sh_session
@jsonapi_required
def pubflow_files_post(pubf_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    body = request.get_json(force=True)
    files = list(filter(lambda f: f["type"] == "files", body["data"]))
    for file in files: # A separate first loop, to make sure given id's are valid
        file["uri"] = get_file_by_id(file["id"])["uri"]
    for file in files:
        create_signing_prep_activity(subcase_uri, file["uri"])
    res = make_response({"data": files}, 202)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

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
@signinghub_machine_session_required # provides g.sh_session
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

@app.route('/publication-flow/<pubf_id>/signing/files/<file_id>/signinghub-iframe-link', methods=['GET'])
@signinghub_machine_session_required # provides g.sh_session
def signinghub_iframe_link(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)["uri"]
    signing_prep = get_signing_prep_from_subcase_file(subcase_uri, file_uri)
    collapse_panels = request.args.get("collapse_panels", default='true', type=str) == "true"
    # import web_pdb; web_pdb.set_trace()
    integration_link = g.sh_session.get_integration_link(signing_prep["sh_package_id"], {
        "language":"nl-NL",
        "user_email": "kaleidos.servicedesk@vlaanderen.be", # Know through scope login?
        "callback_url":"http://localhost:4200/", # default configured fir the app.
        "collapse_panels": "true"
        # "usercertificate_id": "31585" # Undocumented
    })
    return { "url": integration_link }
    return redirect(integration_link, 303)

@app.route('/publication-flow/<pubf_id>/signing/files/<file_id>/start', methods=['POST'])
@signinghub_machine_session_required # provides g.sh_session
def start_signing(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)["uri"]
    signing_prep = get_signing_prep_from_subcase_file(subcase_uri, file_uri)
    g.sh_session.share_document_package(signing_prep["sh_package_id"])
    update_activities_signing_started(signing_prep["uri"])
    return make_response("", 200)


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

