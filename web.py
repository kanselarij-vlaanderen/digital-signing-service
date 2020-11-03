from flask import g, request
from helpers import log
from .authentication import signinghub_session_required

@app.route("/hello")
@signinghub_session_required # provides g.sh_session
def hello():
    return "Hello from the mu-python-template!"
