import json
import sqlite3  # typing only

import flask
import typing
import flask_restful

from .. import schemes
from ..database import db, generate_selector

def merge_dictlike(d1: dict, d2: dict) -> dict:
    d1 = dict(d1)
    d1.update(d2)
    return d2

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
            tables = db.cursor().execute("SELECT name from sqlite_master WHERE type='table'").fetchall()
            return [event['name'] for event in tables if event['name'].startswith(f'frc{season}')]

    class ApiCreate(flask_restful.Resource):
        def put(self, season: int):
            if str(season) not in schemes.MATCH_SCHEME or str(season) not in schemes.PIT_SCHEME:
                return flask_restful.abort(400, description="Invalid Season!")
            if not flask.request.get_data():
                return flask_restful.abort(400)
            event_name = flask.request.get_data().decode('utf8')

            cur: sqlite3.Cursor = db.cursor()
            e, p = schemes.generate_table_schemas(str(season), event_name)
            cur.executescript(e).executescript(p)
            db.connection().commit()
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
            event_id = f"frc{season}{event}"
            input_data = flask.request.get_json(force=True)
            if not input_data:
                return flask_restful.abort(400)
            if input_data["teamNumber"] is None or input_data["name"] is None:
                return flask_restful.abort(400, description="Missing Required Fields")
            
            query = f"INSERT INTO {event_id}_pit ({', '.join(input_data.keys())}) VALUES ({('?, '*len(input_data)).rstrip(', ')})"
            c = db.connection()
            c.execute(query, tuple(input_data.values()))
            c.commit()
            return {"description": "Success!", "teamNumber": input_data['teamNumber']}
            
        def get(self, season, event):
            event_id = f"frc{season}{event}"
            query = "SELECT * FROM {event_id}_pit {query}".format(
                event_id=event_id,
                query=generate_selector(merge_dictlike(flask.request.args, flask.g.args) if hasattr(flask.g, 'args') else flask.request.args)
            )
            values = db.cursor().execute(query)
            if not values:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values.fetchall()]

    class ApiMatch(flask_restful.Resource):
        def post(self, season: int, event: str):
            event_id = f"frc{season}{event}"
            input_data = flask.request.get_json(force=True)
            if not input_data or input_data["teamNumber"] is None or input_data["name"] is None or input_data["form"] is None:
                return flask_restful.abort(400, description="Missing Required Fields")
            submit_data = {}
            for key, value in input_data["form"].items():
                if isinstance(value, dict): #nested dictionary
                    for key1, value1 in value.items():
                        #str.capitalize() and str.title() don't work because they uncapitalize the rest of the string
                        submit_data[key+key1[0].upper()+key1[1:]] = value1
                else: #just a key and value
                    submit_data[key] = value

            query = f"INSERT INTO {event_id}_match ({', '.join(submit_data.keys())}) VALUES ({('?, '*len(submit_data)).rstrip(', ')})"
            c = db.connection()
            #the cursor() function seems unnessecary, but connection.execute is not standard and may not work with different database libraries with a similar api
            c.cursor().execute(query, tuple(submit_data.values()))
            c.commit()
            return {"description": "Success!", "teamNumber": input_data['teamNumber'], "match": input_data['match']}
        
        def get(self, season: int, event: str):
            event_id = f"frc{season}{event}"
            query = "SELECT * FROM {event_id}_match {query}".format(
                event_id=event_id,
                query=generate_selector(merge_dictlike(flask.request.args, flask.g.args) if hasattr(flask.g, 'args') else flask.request.args)
            )
            values = db.cursor().execute(query)
            if not values:
                return flask_restful.abort(404)
            return [dict(scout) for scout in values.fetchall()]