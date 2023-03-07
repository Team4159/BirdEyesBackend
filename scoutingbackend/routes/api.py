import json
import sqlite3  # typing only
import typing

import flask
import flask_restful

from .. import schemes
from ..database import db, generate_selector

from scoutingbackend import schemes
from scoutingbackend.database import db, generate_selector


class Api(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('api', __name__, url_prefix='/api')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.ApiList, '/<int:season>/listEvents')
        self.rest.add_resource(self.ApiCreate, '/<int:season>/createEvent')
        self.rest.add_resource(self.ApiMSchema, '/<int:season>/matchschema')
        self.rest.add_resource(self.ApiPSchema, '/<int:season>/pitschema')
        self.rest.add_resource(self.ApiPit, '/<int:season>/<string:event>/pit')
        self.rest.add_resource(self.ApiMatch, '/<int:season>/<string:event>/match')
    
    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)

    class ApiList(flask_restful.Resource):
        def get(self, season: int):
            tables = db.connection().cursor().execute("SELECT name from sqlite_master WHERE type='table'").fetchall()
            return [event['name'] for event in tables if event['name'].startswith(f'frc{season}')]

    class ApiCreate(flask_restful.Resource):
        def put(self, season: int):
            if str(season) not in schemes.MATCH_SCHEME or str(season) not in schemes.PIT_SCHEME:
                return flask_restful.abort(400, description="Invalid Season!")
            if not flask.request.get_data():
                return flask_restful.abort(400)
            event_name = flask.request.get_data().decode('utf8')

            db.create_tables(season, event_name)
            return {}

    class ApiMSchema(flask_restful.Resource):
        def get(self, season: int):
            if str(season) not in schemes.MATCH_SCHEME:
                return flask_restful.abort(400, description="Invalid Season!")
            return flask.Response(json.dumps(schemes.MATCH_SCHEME[str(season)], sort_keys=False), 200, content_type='application/json')

    class ApiPSchema(flask_restful.Resource):
        def get(self, season: int):
            if str(season) not in schemes.PIT_SCHEME:
                return flask_restful.abort(400, description="Invalid Season!")
            return flask.Response(json.dumps(schemes.PIT_SCHEME[str(season)], sort_keys=False), 200, content_type='application/json')

    class ApiPit(flask_restful.Resource):
        def post(self, season: int, event: str):
            input_data = flask.request.get_json(force=True)
            if not input_data:
                return flask_restful.abort(400)
            if input_data["teamNumber"] is None or input_data["name"] is None:
                return flask_restful.abort(400, description="Missing Required Fields")
            
            c = db.connection()
            c.execute( f"INSERT INTO frc{season}{event}_pit ({', '.join(input_data.keys())}) VALUES ({('?, '*len(input_data)).rstrip(', ')})", tuple(input_data.values()))
            c.commit()
            return {"description": "Success!", "teamNumber": input_data['teamNumber']}
            
        def get(self, season, event):
            values = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_pit {generate_selector(flask.request.args)}")
            if not values:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values.fetchall()]

    class ApiMatch(flask_restful.Resource):
        def post(self, season: int, event: str):
            input_data = flask.request.get_json(force=True)
            if not input_data or input_data["teamNumber"] is None or input_data["name"] is None or input_data["form"] is None:
                return flask_restful.abort(400, description="Missing Required Fields")
            submit_data = {}
            for key, value in input_data.items():
                if isinstance(value, dict): #nested dictionary
                    for key1, value1 in value.items():
                        submit_data[key+key1[0].upper()+key1[1:]] = value1
                else:
                    submit_data[key] = value

            c = db.connection()
            c.cursor().execute(f"INSERT INTO frc{season}{event}_match ({', '.join(submit_data.keys())}) VALUES ({('?, '*len(submit_data)).rstrip(', ')})", tuple(submit_data.values()))
            c.commit()
            return {"description": "Success!", "teamNumber": input_data['teamNumber'], "match": input_data['match']}
        
        def get(self, season: int, event: str):
            values = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_match {generate_selector(flask.request.args)}")
            if not values:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values.fetchall()]