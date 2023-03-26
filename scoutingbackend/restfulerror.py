import flask_restful
import flask
import json
class RestfulErrorApi(flask_restful.Api):
    def handle_error(self, e: Exception):
        if isinstance(e, flask_restful.HTTPException):
            print("bruh")
            return super().handle_error(e)
        else:
            print("NOT BRUH")
            return_data = {
                "description": f"Uncaught Error ({type(e).__name__}): {str(e)}",
            }
            return flask.Response(json.dumps(return_data), 500)