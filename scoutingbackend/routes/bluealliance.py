import contextvars
import datetime
import json
import sqlite3  # typing only

import flask
import flask_restful
import requests

from .. import schemes
from ..database import db

session = requests.Session() #SHOULD REALLY BE A CONTEXT-SENSITIVE VARIABLE BUT WHATEVER

class BlueAlliance(object):
    def __init__(self, api_key: str) -> None:
        #session.set(requests.Session()) #change me with custom cacher
        session.headers['X-TBA-Auth-Key'] = api_key
        
        self.bp = flask.Blueprint('ba', __name__, url_prefix='/bluealliance')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.BAIndex, '/')
        self.rest.add_resource(self.BASeason, '/<int:season>')
        self.rest.add_resource(self.BAEvent, '/<int:season>/<string:event>')
        self.rest.add_resource(self.BAMatch, '/<int:season>/<string:event>/<string:match>')
    
    def register(self, app: flask.Flask | flask.Blueprint):
        app.register_blueprint(self.bp)
    
    @staticmethod
    def is_valid_event(event: dict, ignore_date=False):
        start_date = datetime.datetime.strptime(event['start_date'], r"%Y-%m-%d",).date()
        end_date = datetime.datetime.strptime(event['end_date'], r"%Y-%m-%d").date()
        today = datetime.date.today()
        return event['state_prov'] == flask.current_app.config['TBA_STATE'] and (ignore_date or start_date <= today <= end_date)
    
    class BAIndex(flask_restful.Resource):
        def get(self):
            resp = session.get("https://www.thebluealliance.com/api/v3/status")
            if resp.status_code != 200:
                return flask_restful.abort(resp.status_code)
            respj = resp.json()
            return {"max_season": respj['max_season'], "current_season": respj['current_season']}
            
    class BASeason(flask_restful.Resource):
        def get(self, season: int):
            ignore_date = flask.request.args.get('ignoreDate', "false").lower()=="true"
            resp = session.get(f"https://www.thebluealliance.com/api/v3/events/{season}/simple")
            if resp.status_code != 200:
                return flask_restful.abort(resp.status_code)
            j = resp.json()
            return {e['event_code']: e['name'] for e in filter(lambda b: BlueAlliance.is_valid_event(b, ignore_date), j)}
    
    class BAEvent(flask_restful.Resource):
        def get(self, season: int, event: str):
            resp = session.get(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/matches/simple")
            if resp.status_code != 200:
                return flask_restful.abort(resp.status_code)
            j = resp.json()
            return {e['key'].split("_")[-1]: e['key'] for e in j}
        
    class BAMatch(flask_restful.Resource):
        def get(self, season: int, event: str, match: str):
            match_code = f"{season}{event}_{match}"
            resp = session.get(f"https://www.thebluealliance.com/api/v3/match/{match_code}/simple")
            if resp.status_code != 200:
                return flask_restful.abort(resp.status_code)
            j = resp.json()
            if 'Error' in j:
                return flask_restful.abort(401, description=j['Error'])
            a = j['alliances']
            o = {}
            for alliance in a.keys():
                for teamCode in a[alliance]['team_keys']:
                    o[teamCode[3:]] = alliance
            return o