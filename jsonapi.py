import typing

from functools import wraps
from flask import request
from helpers import error

def header_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.content_type != "application/vnd.api+json":
            return error("This endpoint requires the content-type of the request to be of type 'application/vnd.api+json'", 415)
        return f(*args, **kwargs)
    return decorated_function

# https://jsonapi.org/format/#document-resource-object-identification
class ResourceIdentification(typing.TypedDict):
    id: str
    type: str

def require_identification(data: typing.Dict, required_resource_type_name: typing.Union[str, None] = None) -> ResourceIdentification:
    if not isinstance(data["id"], str):
        raise ValueError()
    if not isinstance(data["type"], str):
        raise ValueError()

    if required_resource_type_name and data["type"] != required_resource_type_name:
        raise ValueError()

    return typing.cast(ResourceIdentification, data)