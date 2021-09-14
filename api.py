import traceback
import functools
import flask
import helpers

class NotFoundException(Exception):
    def __init__(self, url):
        super().__init__("Resource not found: " + url)

class InvalidStateException(Exception):
    pass

def route(*args, **kwargs):
    
    def decorator(f):
        @app.route(*args, **kwargs)
        @functools.wraps(f) # necessary for Flask to realize it's not routing to the same decorated_function
        def decorated_function(*args, **kwargs):
            # if request.content_type != "application/vnd.api+json":
            #    return helpers.error("This endpoint requires the content-type of the request to be of type 'application/vnd.api+json'", 415)

            try:
                response_data = f(*args, **kwargs)
                if isinstance(response_data, int):
                    status = response_data
                    body = ""
                elif isinstance(response_data, tuple):
                    status, data = response_data
                    body = { "data": data }
                else:
                    helpers.log(type(response_data))
                    raise Exception(f"incorrect return type: {type(response_data)}")

                response = flask.make_response(body, status)
                response.headers["Content-Type"] = "application/vnd.api+json"
                return response

            except NotFoundException as not_found:
                return helpers.error(not_found.args, 404)
            except InvalidStateException as invalid_state:
                return helpers.error(invalid_state.args, 400)
            except Exception: # pylint: disable=broad-except
                traceback.print_exc()
                return helpers.error("Internal Server Error", 500)

        return decorated_function

    return decorator
