import os
from datetime import date, datetime

from flask import Blueprint, Response, abort, request, current_app, Flask
from requests import Session
from functools import wraps
from .. import db

class RequestCacher(object):
    def __init__(self, tba_key: str | None = None) -> None:
        self.session = Session()
        if tba_key:
            self.session.headers['X-TBA-Auth-Key'] = tba_key
    
    def get_json(self, *args, **kwargs):
        pass

session_ = Session()

class BlueAllianceRoutes(object):

    bp = Blueprint('bluealliance', __name__, url_prefix='/bluealliance')

    def __init__(self, tba_key: str | None) -> None:
        self.tba_key = tba_key
        #session_ = Session()
        if tba_key:
            session_.headers['X-TBA-Auth-Key'] = tba_key

    def register(self, app: Flask | Blueprint):
        app.register_blueprint(self.bp)

    @staticmethod
    def is_valid_event(event: dict, ignore_date=False):
        start_date = datetime.strptime(event['start_date'], r"%Y-%m-%d",).date()
        end_date = datetime.strptime(event['end_date'], r"%Y-%m-%d").date()
        today = date.today()
        return event['state_prov'] == os.getenv('TBA_STATE') and (ignore_date or start_date <= today <= end_date)
    

    @bp.route("/", methods=("GET",))
    def route_current():
        resp = session_.get("https://www.thebluealliance.com/api/v3/status")
        if resp.status_code == 401:
            return abort(401)
        e = resp.json()
        return {"max_season": e['max_season'], "current_season": e['current_season']}

    @bp.route('/<season>/', methods=("GET",))
    def current_events(season):
        resp = session_.get(f"https://www.thebluealliance.com/api/v3/events/{season}/simple")
        if resp.status_code == 401:
            return abort(401)
        j = resp.json()
        return {e['event_code']: e['name'] for e in filter(lambda b: BlueAllianceRoutes.is_valid_event(b, request.args.get('ignoreDate', "false").lower()=="true"), j)}

    @bp.route('/<season>/<event>/', methods=("GET",))
    def current_matches(season, event):
        resp = session_.get(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/matches/simple")
        if resp.status_code == 401:
            return abort(401)
        j = resp.json()
        return {e['key'].split("_")[-1]: e['key'] for e in j}

    @bp.route('/<season>/<event>/<match>/', methods=("GET",))
    def match_info(season, event, match):
        matchCode = season+event+"_"+match
        resp = session_.get(f"https://www.thebluealliance.com/api/v3/match/{matchCode}/simple")
        if resp.status_code == 401:
            return abort(401)
        j = resp.json()
        if 'Error' in j:
            return abort(Response(j['Error'], 401))
        a = j['alliances']
        o = {}
        for alliance in a.keys():
            for teamCode in a[alliance]['team_keys']:
                o[teamCode[3:]] = alliance
        return o
