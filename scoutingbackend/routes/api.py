import csv
from io import StringIO
import json
import typing

import flask
import flask_restful

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
        self.rest.add_resource(self.ApiMatch, '/<int:season>/<string:event>/match')
        self.rest.add_resource(self.ApiPit, '/<int:season>/<string:event>/pit')
        self.rest.add_resource(self.ApiCsvMatch, '/<int:season>/<string:event>/matchcsv')
        
        self.list = self.ApiList()
        self.create = self.ApiCreate()
        self.match_schema = self.ApiMSchema()
        self.pit_schema = self.ApiPSchema()
        self.match = self.ApiMatch()
        self.pit = self.ApiPit()
    
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
                return flask_restful.abort(400, description="No event set")
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
            if f"frc{season}{event}_pit" not in [e['name'] for e in c.execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.Response("table not exist", 404)
            c.cursor().execute( f"INSERT INTO frc{season}{event}_pit ({', '.join(input_data.keys())}) VALUES ({('?, '*len(input_data)).rstrip(', ')})", tuple(input_data.values()))
            c.commit()
            return {"description": "Success!", "teamNumber": input_data['teamNumber']}
            
        def get(self, season, event):
            if f"frc{season}{event}_pit" not in [e['name'] for e in db.connection().cursor().execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.Response("table not exist", 404)
            values = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_pit {generate_selector(flask.request.args)}")
            if not values:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values.fetchall()]

    class ApiMatch(flask_restful.Resource):
        def post(self, season: int, event: str):
            input_data = flask.request.get_json(force=True)
            if not input_data or input_data["teamNumber"] is None or input_data["name"] is None:
                return flask_restful.abort(400, description="Missing Required Fields")
            submit_data = {}
            for key, value in input_data.items():
                if isinstance(value, dict):
                    for key1, value1 in value.items():
                        submit_data[key+key1[0].upper()+key1[1:]] = value1
                else:
                    submit_data[key] = value

            c = db.connection()
            if f"frc{season}{event}_match" not in [e['name'] for e in c.execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.Response("Table does not exist.", 404)
            c.cursor().execute(f"INSERT INTO frc{season}{event}_match ({', '.join(submit_data.keys())}) VALUES ({('?, '*len(submit_data)).rstrip(', ')})", tuple(submit_data.values()))
            c.commit()
            return {"description": "Success!", "teamNumber": input_data['teamNumber'], "match": input_data['match']}
        
        def get(self, season: int, event: str):
            if f"frc{season}{event}_match" not in [e['name'] for e in db.connection().cursor().execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.Response("Table does not exist.", 404)
            values = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_match {generate_selector(flask.request.args)}")
            if not values:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values.fetchall()]
    
    class ApiCsvMatch(flask_restful.Resource): #this is to be kept for emergency purposes, e.g. something goes wrong with analysis or if we just want a full look at all of the data
        def get(self, season: int, event: str):
            if f"frc{season}{event}_match" not in [e['name'] for e in db.connection().cursor().execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.Response("table not exist", 404)
            print(generate_selector(flask.request.args))
            data = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_match {generate_selector(flask.request.args)}").fetchall()
            output_io = StringIO()

            writer = csv.writer(output_io)
            try:
                writer.writerows([list(data[0].keys())]+data)
            except IndexError:
                return flask_restful.abort(406, description="no data is available", tip="did you make sure the filters were correct?")
            return flask.Response(output_io.getvalue(), 200, mimetype='text/csv')