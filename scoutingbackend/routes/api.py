import json
import sqlite3  # typing only

import flask
import flask_restful

from .. import schemes
from ..database import db

class Api(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('api', __name__, url_prefix='/api')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.ApiList, '/<int:season>/listEvents')
        self.rest.add_resource(self.ApiCreate, '/<int:season>/createEvents')
        self.rest.add_resource(self.ApiMSchema, '/<int:season>/matchschema')
        self.rest.add_resource(self.ApiPSchema, '/<int:season>/pitschema')
        self.rest.add_resource(self.ApiPit, '/<int:season>/<string:event>/pit')
        self.rest.add_resource(self.ApiMatch, '/<int:season>/<string:event>/match')
    
    def register(self, app: flask.Flask | flask.Blueprint):
        app.register_blueprint(self.bp)

    class ApiList(flask_restful.Resource):
        def get(self, season: int):
            tables = db.cursor().execute("SELECT name from sqlite_master WHERE type='table'").fetchall()
            return [event['name'] for event in tables if event['name'].startswith(f'frc{season}')]

    class ApiCreate(flask_restful.Resource):
        def put(self, season: int):
            #Should probably change input type from raw data with event to something else but eh
            if str(season) not in schemes.MATCH_SCHEME or str(season) not in schemes.PIT_SCHEME:
                return flask_restful.abort(400, description="invalid season")
            if not flask.request.get_data():
                return flask_restful.abort(400, description="bad event data")
            event_name = flask.request.get_data().decode('utf8')
            cur: sqlite3.Cursor = db.cursor()
            e, p = schemes.generate_table_schemas(str(season), event_name)
            cur.executescript(e)
            cur.executescript(p)
            db.connection().commit()
            return {}

    class ApiMSchema(flask_restful.Resource):
        def get(self, season: int):
            if str(season) not in schemes.MATCH_SCHEME:
                return flask_restful.abort(400, description="invalid season")
            #workaround for unsorted json
            return flask.Response(json.dumps(schemes.MATCH_SCHEME[str(season)], sort_keys=False), 200, content_type='application/json')

    class ApiPSchema(flask_restful.Resource):
        def get(self, season: int):
            if str(season) not in schemes.PIT_SCHEME:
                return flask_restful.abort(400, description="invalid season")
            #workaround for unsorted json
            return flask.Response(json.dumps(schemes.PIT_SCHEME[str(season)], sort_keys=False), 200, content_type='application/json')

    class ApiPit(flask_restful.Resource):
        def post(self, season: int, event: str):
            event_id = f"frc{season}{event}"
            input_data = flask.request.get_json(force=True)
            if not input_data:
                return flask_restful.abort(400, description="no input given")
            if input_data["teamNumber"] is None or input_data["name"] is None:
                return flask_restful.abort(400, description="missing required fields")
            query = f"INSERT INTO {event_id}_pit (teamNumber, {', '.join(schemes.PIT_SCHEME[str(season)].values())}) VALUES ({('?, '*len(input_data)).rstrip(', ')})"
            db.cursor().execute(query, tuple(input_data.values()))
            db.connection().commit()
            return {"description": "successfully added pit response", "teamNumber": input_data['teamNumber']}
            
        def get(self, season, event):
            event_id = f"frc{season}{event}"
            query = "SELECT * FROM {event_id}_pit {query}".format(
                event_id=event_id,
                query='WHERE ' + ' AND '.join(f'{k}="{v}"' for k,v in flask.request.args.items()) if len(flask.request.args) else ""
            )
            values = db.cursor().execute(query)
            if not values:
                return flask_restful.abort(404, description="event not found in database")
            return [dict(scout) for scout in values.fetchall()]

    class ApiMatch(flask_restful.Resource):
        def post(self, season: int, event: str):
            event_id = f"frc{season}{event}"
            input_json = flask.request.get_json(force=True)
            if not input_json:
                return flask_restful.abort(400, description="no input given")
            if input_json["teamNumber"] is None or input_json["scouter"] is None:
                return flask_restful.abort(400, description="missing required fields")
            submit_data = {}
            for key, value in input_json.items():
                if isinstance(value, dict):
                    for key1, value1 in value:
                        submit_data[key+key1.capitalize()] = value1
                else:
                    submit_data[key] = value
            #TODO: could probably use sqlite variable substitution
            db.cursor().execute(f"INSET INTO {event_id}_match ({', '.join(submit_data.keys())}) VALUES ({('?, '*len(submit_data)).rstrip(', ')})",
                                    tuple(submit_data.values()))
            db.connection().commit()
            return {"description": "successfully added match response", "teamNumber": input_json['teamNumber'], "matchNumber": input_json['match']}
        
        def get(self, season: int, event: str):
            event_id = f"frc{season}{event}"
            query = "SELECT * FROM {event_id}_match {query}".format(
                event_id=event_id,
                query='WHERE ' + ' AND '.join(f'{k}="{v}"' for k,v in flask.request.args.items()) if len(flask.request.args) else ""
            )
            values = db.cursor().execute(query)
            if not values:
                return flask_restful.abort(404, description="event not found in database")
            return [dict(scout) for scout in values.fetchall()]