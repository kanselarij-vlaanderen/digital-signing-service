from flask import g, request, make_response
from helpers import log
from .authentication import signinghub_session_required
from .lib.pub_flow import get_subcase_from_pub_flow_id
from .lib.activity import get_signing_preps_from_subcase, create_signing_prep_activity
from .lib.file import get_file_by_id

@app.route("/hello")
@signinghub_session_required # provides g.sh_session
def hello():
    return "Hello from the mu-python-template!"


@app.route('/publication-flow/<uuid:pubf_id>/signing/files', methods=['GET', 'POST'])
@signinghub_session_required # provides g.sh_session
def pubflow_files(pubf_id):
    subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
    if request.method == 'GET':
        try:
            signing_preps = get_signing_preps_from_subcase(subcase_uri)
            files = []
            for signing_prep in signing_preps:
                files.append({
                    "type": "files",
                    "id": signing_prep["file_id"]
                })
        except Exception: # No signing preps available
            files = []
        res = make_response({"data": files})
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res
    if request.method == 'POST':
        body = request.get_json(force=True)
        files = filter(lambda f: f["type"] == "files", body["data"])
        for file in files: # A separate first loop, to make sure given id's are valid
            file["uri"] = get_file_by_id(file["id"])
        for file in files:
            create_signing_prep_activity(subcase_uri, file["uri"])
        res = make_response({"data": files}, 202)
        res.headers["Content-Type"] = "application/vnd.api+json"
        return res


