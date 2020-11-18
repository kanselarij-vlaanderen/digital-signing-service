from functools import wraps
from flask import request
from helpers import error

def jsonapi_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.content_type != "application/vnd.api+json":
            return error("This endpoint requires the content-type of the request to be of type 'application/vnd.api+json'", 415)
        return f(*args, **kwargs)
    return decorated_function
