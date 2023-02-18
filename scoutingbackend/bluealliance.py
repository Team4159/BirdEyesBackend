import os
from datetime import date, datetime

from flask import Blueprint, Response, abort, request
from flask_cors import cross_origin
from requests import Session

request_session = Session()
request_session.headers['X-TBA-Auth-Key'] = os.getenv('TBA_KEY')

bp = Blueprint('bluealliance', __name__, url_prefix='/bluealliance')

# TODO: These need to be perma-cached for offline use
def is_valid_event(event: dict, ignore_date=False):
    start_date = datetime.strptime(event['start_date'], r"%Y-%m-%d",).date()
    end_date = datetime.strptime(event['end_date'], r"%Y-%m-%d").date()
    today = date.today()
    return event['state_prov'] == os.getenv('TBA_STATE') and (ignore_date or start_date <= today <= end_date)

@bp.route("/", methods=("GET",))
def current_seasons():
    resp = request_session.get("https://www.thebluealliance.com/api/v3/status")
    if resp.status_code == 401:
        return abort(401)
    e = resp.json()
    return {"max_season": e['max_season'], "current_season": e['current_season']}

@bp.route('/<season>/', methods=("GET",))
def current_events(season):    
    resp = request_session.get(f"https://www.thebluealliance.com/api/v3/events/{season}/simple")
    if resp.status_code == 401:
        return abort(401)
    return {e['event_code']: e['name'] for e in filter(lambda b: is_valid_event(b, request.args.get('ignoreDate', False)), resp.json())}

@bp.route('/<season>/<event>/', methods=("GET",))
def current_matches(season, event):
    resp = request_session.get(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/matches/simple")
    if resp.status_code == 401:
        return abort(401)
    return {e['key'].split("_")[-1]: e['key'] for e in resp.json()}

@bp.route('/<season>/<event>/<match>/', methods=("GET",))
def match_info(season, event, match):
    matchCode = season+event+"_"+match
    resp = request_session.get(f"https://www.thebluealliance.com/api/v3/match/{matchCode}/simple")
    if resp.status_code == 401:
        return abort(401)
    if 'Error' in resp:
        return abort(Response(resp['Error'], 401))
    a = resp.json()['alliances']
    o = {}
    for alliance in a.keys():
        for teamCode in a[alliance]['team_keys']:
            o[teamCode[3:]] = alliance
    return o
