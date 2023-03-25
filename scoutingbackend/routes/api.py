import csv
from io import StringIO
import json
from sqlite3 import OperationalError
import typing

import flask
import flask_restful

from scoutingbackend import schemes
from scoutingbackend.database import db, generate_selector


class Api(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('api', __name__, url_prefix='/api')

        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.Tables, '/<int:season>/tables')
        self.rest.add_resource(self.ApiMSchema, '/<int:season>/matchschema')
        self.rest.add_resource(self.ApiPSchema, '/<int:season>/pitschema')
        self.rest.add_resource(self.ApiPit, '/<int:season>/<string:event>/pit')
        self.rest.add_resource(self.ApiPitCsv, '/<int:season>/<string:event>/pit/csv')
        self.rest.add_resource(self.ApiMatch, '/<int:season>/<string:event>/match')
        
        self.tables = self.Tables()
        self.match_schema = self.ApiMSchema()
        self.pit_schema = self.ApiPSchema()
        self.match = self.ApiMatch()
        self.pit = self.ApiPit()

    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)

    class Tables(flask_restful.Resource):
        def get(self, season: int):
            tables = db.connection().cursor().execute("SELECT name from sqlite_master WHERE type='table'").fetchall()
            return [event['name'] for event in tables if season <= 0 or event['name'].startswith(f'frc{season}')]
        
        def put(self, season: int):
            if str(season) not in schemes.MATCH_SCHEME or str(season) not in schemes.PIT_SCHEME:
                return flask_restful.abort(400, description="Invalid Season!")
            if not flask.request.get_data():
                return flask_restful.abort(400, description="No Event Set!")
            event_name = flask.request.get_data().decode(flask.request.charset)

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
                return flask.Response("Table does not exist.", 404)
            c.cursor().execute( f"INSERT INTO frc{season}{event}_pit ({', '.join(input_data.keys())}) VALUES ({('?, '*len(input_data)).rstrip(', ')})", tuple(input_data.values()))
            c.commit()
            return {"description": "Success!", "teamNumber": input_data['teamNumber']}
            
        def get(self, season, event):
            if f"frc{season}{event}_pit" not in [e['name'] for e in db.connection().cursor().execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.Response("Table does not exist.", 404)
            try:
                values = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_pit {generate_selector(flask.request.args)}").fetchall()
            except OperationalError:
                return flask_restful.abort(400, description="Invalid Selectors")
            if len(values) == 0:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values]
        
        def patch(self, season: int, event: str):
            input_data = flask.request.get_json(force=True)
            if not input_data:
                return flask_restful.abort(400)
            if "teamNumber" not in input_data or input_data["teamNumber"] is None:
                return flask_restful.abort(400, description="Missing Team Number")
            if "name" not in input_data or input_data["name"] is None:
                return flask_restful.abort(400, description="Missing Name")
            if "edits" not in input_data or input_data["edits"] is None or type(input_data["edits"]) is not dict or len(input_data["edits"]) < 1:
                return flask.Response("No Edits Made", 204)
            
            c = db.connection()
            if f"frc{season}{event}_pit" not in [e["name"] for e in c.cursor().execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.abort(404, f"Table frc{season}{event}_pit Does Not Exist")
            
            row = c.cursor().execute("SELECT * FROM frc{}{}_pit WHERE teamNumber={} AND name='{}'".format(season, event, input_data["teamNumber"], input_data["name"])).fetchone()
            if row is None:
                return flask_restful.abort(400, description="Pit Scouting Response Not Found For Team: {} By Scouter: {}".format(input_data["teamNumber"], input_data["name"]))
            if not all(key in row.keys() for key in input_data["edits"]):
                return flask_restful.abort(400, description=f"Invalid Edit: One or More Keys Not Found")
            
            c.cursor().execute("UPDATE frc{}{}_pit SET {} WHERE teamNumber={} AND name='{}'".format(season, event, ", ".join([f"{k}='{v}'" for k, v in input_data["edits"].items()]), input_data["teamNumber"], input_data["name"]))
            c.commit()
            return {"description": "Successfully Edited Pit Scouting Response For Team: {} By Scouter: {}".format(input_data["teamNumber"], input_data["name"])}
    
    class ApiPitCsv(flask_restful.Resource):
        def get(self, season: int, event: str):
            if f"frc{season}{event}_pit" not in [e['name'] for e in db.connection().cursor().execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()]:
                return flask.Response("Table does not exist.", 404)
            try:
                values = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_pit {generate_selector(flask.request.args)}").fetchall()
            except OperationalError:
                return flask_restful.abort(400, description="Invalid Selectors")
            if len(values) == 0:
                return flask_restful.abort(404)
            out = StringIO()
            writer = csv.DictWriter(out, fieldnames=["name", "teamNumber", *schemes.PIT_SCHEME[str(season)].keys()])
            writer.writeheader()
            writer.writerows([{k: v for (k, v) in dict(scout).items() if k in writer.fieldnames} for scout in values])
            return flask.Response(out.getvalue(), 200, mimetype='text/csv')

    class ApiMatch(flask_restful.Resource):
        def post(self, season: int, event: str):
            input_data = flask.request.get_json(force=True)
            if not input_data or input_data["teamNumber"] is None or input_data["name"] is None:
                return flask.abort(400, description="Missing Required Fields")
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
            try:
                values = db.connection().cursor().execute(f"SELECT * FROM frc{season}{event}_match {generate_selector(flask.request.args)}").fetchall()
            except OperationalError:
                return flask_restful.abort(400, description="Invalid Selectors")
            if not values:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values]