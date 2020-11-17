from flask import g, request, make_response
from helpers import log
from .authentication import signinghub_session_required
from .lib.pub_flow import get_subcase_from_pub_flow_id
from .lib.activity import get_signing_preps_from_subcase

@app.route("/hello")
@signinghub_session_required # provides g.sh_session
def hello():
    return "Hello from the mu-python-template!"


@app.route('/publication-flow/<uuid:pubf_id>/signing/files', methods=['GET', 'POST'])
@signinghub_session_required # provides g.sh_session
def pubflow_files(pubf_id):
    if request.method == 'GET':
        subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
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

