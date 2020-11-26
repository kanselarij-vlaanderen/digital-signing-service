from flask import g, request, make_response, redirect
from helpers import log
from .authentication import signinghub_session_required
from .jsonapi import jsonapi_required
from .lib.pub_flow import get_subcase_from_pub_flow_id
from .lib.activity import get_signing_preps_from_subcase, \
    get_signing_prep_from_subcase_file, \
    create_signing_prep_activity, \
    add_signing_activity
from .lib.file import get_file_by_id
from .lib.mandatee import get_mandatee_by_id, get_signing_mandatees
from .lib.exceptions import NoQueryResultsException

@app.route("/signinghub-profile")
@signinghub_session_required # provides g.sh_session
def sh_profile_info():
    """Maintenance endpoint for debugging SigningHub authentication"""
    return g.sh_session.get_general_profile_information()

@app.route('/publication-flow/<uuid:pubf_id>/signing/files', methods=['GET'])
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

@app.route('/publication-flow/<uuid:pubf_id>/signing/files', methods=['POST'])
@signinghub_session_required # provides g.sh_session
@jsonapi_required
def pubflow_files_post(pubf_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    body = request.get_json(force=True)
    files = filter(lambda f: f["type"] == "files", body["data"])
    for file in files: # A separate first loop, to make sure given id's are valid
        file["uri"] = get_file_by_id(file["id"])
    for file in files:
        create_signing_prep_activity(subcase_uri, file["uri"])
    res = make_response({"data": files}, 202)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/publication-flow/<uuid:pubf_id>/signing/files/<uuid:file_id>/signers', methods=['GET'])
def file_signers_get(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)
    sig_prep_act = get_signing_prep_from_subcase_file(subcase_uri, file_uri)
    try:
        mandatees = get_signing_mandatees(sig_prep_act)
        mandatees_data = []
        for mandatee in mandatees:
            mandatees_data.append({
                "type": "mandatees",
                "id": mandatee["id"]
            })
        status_code = 200
    except NoQueryResultsException: # No mandatees available
        mandatees_data = []
        status_code = 404
    res = make_response({"data": mandatees_data}, status_code)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/publication-flow/<uuid:pubf_id>/signing/files/<uuid:file_id>/signers', methods=['POST'])
@signinghub_session_required # provides g.sh_session
@jsonapi_required
def file_signers_post(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)
    body = request.get_json(force=True)
    mandatees = filter(lambda f: f["type"] == "mandatees", body["data"])
    for mandatee in mandatees: # A separate first loop, to make sure given id's are valid
        mandatee["uri"] = get_mandatee_by_id(mandatee["id"])
    for mandatee in mandatees:
        add_signing_activity(subcase_uri, file_uri, mandatee["uri"])
    res = make_response({"data": mandatees}, 202)
    res.headers["Content-Type"] = "application/vnd.api+json"
    return res

@app.route('/publication-flow/<uuid:pubf_id>/signing/files/<uuid:file_id>/signinghub-iframe-link', methods=['GET'])
@signinghub_session_required # provides g.sh_session
def signinghub_iframe_link(pubf_id, file_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    file_uri = get_file_by_id(file_id)
    signing_prep = get_signing_prep_from_subcase_file(subcase_uri, file_uri)
    collapse_panels = request.args.get("collapse_panels", default='true', type=str)
    integration_link = g.sh_session.get_integration_link(signing_prep["sh_package_id"], {
        "language":"nl-NL",
        # "user_email": "joe@gmail.com", # Know through SSO login?
        # "callback_url":"https://web.signinghub.com/", # default configured fir the app.
        "collapse_panels": "true" if collapse_panels == "true" else "false",
        # "usercertificate_id": "31585" # Undocumented
    })
    redirect(integration_link, 303)

