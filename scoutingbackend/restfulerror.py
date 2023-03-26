import flask_restful
import flask

class RestfulErrorApi(flask_restful.Api):
    def handle_error(self, e: Exception):
        if isinstance(e, flask_restful.HTTPException):
            return super().handle_error(e)
        print(f"Uncaught {type(e).__name__}: {e}")
        return flask.Response(status=500)