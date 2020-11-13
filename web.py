from flask import g, request
from helpers import log
from .authentication import signinghub_session_required
from .lib.pub_flow import get_subcase_from_pub_flow_id

@app.route("/hello")
@signinghub_session_required # provides g.sh_session
def hello():
    return "Hello from the mu-python-template!"


@app.route('/publication-flow/<uuid:pubf_id>/signing/documents', methods=['GET', 'POST'])
@signinghub_session_required # provides g.sh_session
def pubflow_documents(pubf_id):
    if request.method == 'GET':
        subcase_uri = get_subcase_from_pub_flow_id(pubf_id)["uri"]
        # TODO
