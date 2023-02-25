import contextvars
import datetime
import time
import urllib.parse
import json
import os
import pathlib
import sqlite3  # typing only

import flask
import werkzeug.datastructures
import flask_restful
import requests

from .. import schemes
from .. import database

class CachingSession(requests.Session):
    def __init__(self, manual_cache: os.PathLike | str | None = None) -> None:
        super().__init__()
        if manual_cache:
            self.cache_path = pathlib.Path(manual_cache)
        else:
            self.cache_path = None
    
    def set_manual_cache(self, manual_cache: os.PathLike | str):
        self.cache_path = pathlib.Path(manual_cache)
    
    def generate_response(self, data: bytes, code: int = 200):
        '''Generates a semi-fake requests response'''
        resp = requests.Response()
        resp.status_code = code
        resp._content = data
        return resp
    
    def get(self, url: str, cache_control: werkzeug.datastructures.RequestCacheControl | None = None, **kwargs) -> requests.Response:
        parsed_url = urllib.parse.urlparse(url)
        if 'thebluealliance.com' not in parsed_url.netloc: #not BA
            return super().get(url, **kwargs)
        if not self.cache_path or not cache_control: #cache not enabled #DO NOT MERGE INTO THE TOP STATEMENT, IT IS SPLIT FOR READABILITY
            return super().get(url, **kwargs)
        path_list = parsed_url.path.split("/")[3:]
        cache_path = pathlib.Path(self.cache_path, *path_list[:-1], f"{path_list[-1]}.json")
        if cache_path.exists() and not cache_control.no_cache:
            cache_json = json.loads(cache_path.read_text())
            real_data = json.dumps(cache_json['data']).encode('utf8')
            if 'last-update' in cache_json and (cache_control.max_age is None or time.time() - cache_json['last-update'] <= cache_control.max_age):
                return self.generate_response(real_data, code=cache_json['code'] if 'code' in cache_json else 200)
            #if the response isn't new enough let the if-statement fall back to manually requesting and caching
        resp = super().get(url, **kwargs)
        if cache_control.no_store or not self.cache_path.is_dir():
            return resp
        cached_data = {
            "last-update": time.time(),
            "code": resp.status_code,
            "data": resp.json()
        }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cached_data))
        return resp

session = CachingSession() #SHOULD REALLY BE A CONTEXT-SENSITIVE VARIABLE BUT WHATEVER

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
            resp = session.get("https://www.thebluealliance.com/api/v3/status", cache_control=flask.request.cache_control)
            if resp.status_code != 200:
                return flask_restful.abort(resp.status_code)
            respj = resp.json()
            open("TEST.json", 'wb+').write(resp.content)
            return {"max_season": respj['max_season'], "current_season": respj['current_season']}
            
    class BASeason(flask_restful.Resource):
        def get(self, season: int):
            ignore_date = flask.request.args.get('ignoreDate', "false").lower()=="true"
            resp = session.get(f"https://www.thebluealliance.com/api/v3/events/{season}/simple", cache_control=flask.request.cache_control)
            if resp.status_code != 200:
                return flask_restful.abort(resp.status_code)
            j = resp.json()
            return {e['event_code']: e['name'] for e in filter(lambda b: BlueAlliance.is_valid_event(b, ignore_date), j)}
    
    class BAEvent(flask_restful.Resource):
        def get(self, season: int, event: str):
            resp = session.get(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/matches/simple", cache_control=flask.request.cache_control)
            if resp.status_code != 200:
                return flask_restful.abort(resp.status_code)
            j = resp.json()
            return {e['key'].split("_")[-1]: e['key'] for e in j}
        
    class BAMatch(flask_restful.Resource):
        def get(self, season: int, event: str, match: str):
            match_code = f"{season}{event}_{match}"
            resp = session.get(f"https://www.thebluealliance.com/api/v3/match/{match_code}/simple", cache_control=flask.request.cache_control)
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