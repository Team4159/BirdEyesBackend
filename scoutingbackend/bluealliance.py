import os
from datetime import date, datetime

from flask import Blueprint, Response, abort, request
from requests import Session
from . import db

request_session = Session()
request_session.headers['X-TBA-Auth-Key'] = os.getenv('TBA_KEY') #type:ignore

bp = Blueprint('bluealliance', __name__, url_prefix='/bluealliance')


# TODO: These need to be perma-cached for offline use
def is_valid_event(event: dict, ignore_date=False):
    start_date = datetime.strptime(event['start_date'], r"%Y-%m-%d",).date()
    end_date = datetime.strptime(event['end_date'], r"%Y-%m-%d").date()
    today = date.today()
    return event['state_prov'] == os.getenv('TBA_STATE') and (ignore_date or start_date <= today <= end_date)

@bp.route("/", methods=("GET",))
def current_seasons():
    ba_cache = db.get_connector().create_simple("blueallianceCache")
    cache_enabled = request.args.get("cache", "true") == "true"
    refresh_cache = request.args.get("refresh", "false") == "true"
    if ba_cache.contains(route="status") and cache_enabled and not refresh_cache:
        e = ba_cache.uncache("route", "status", "data")
    else:
        resp = request_session.get("https://www.thebluealliance.com/api/v3/status")
        if resp.status_code == 401:
            return abort(401)
        e = resp.json()
        if cache_enabled:
            ba_cache.cache("route", "status", "data", e)
    return {"max_season": e['max_season'], "current_season": e['current_season']}

@bp.route('/<season>/', methods=("GET",))
def current_events(season):    
    ba_cache = db.get_connector().create_simple("blueallianceCache")
    cache_enabled = request.args.get("cache", "true") == "true"
    refresh_cache = request.args.get("refresh", "false") == "true"
    if ba_cache.contains(route=f"events/{season}/simple") and cache_enabled and not refresh_cache:
        j = ba_cache.uncache("route", f"events/{season}/simple", "data")
    else:
        resp = request_session.get(f"https://www.thebluealliance.com/api/v3/events/{season}/simple")
        if resp.status_code == 401:
            return abort(401)
        j = resp.json()
        if cache_enabled:
            ba_cache.cache("route", f"events/{season}/simple", "data", j)
    return {e['event_code']: e['name'] for e in filter(lambda b: is_valid_event(b, request.args.get('ignoreDate', "false").lower()=="true"), j)}

@bp.route('/<season>/<event>/', methods=("GET",))
def current_matches(season, event):
    ba_cache = db.get_connector().create_simple("blueallianceCache")
    cache_enabled = request.args.get("cache", "true") == "true"
    refresh_cache = request.args.get("refresh", "false") == "true"
    print(cache_enabled, refresh_cache)
    if ba_cache.contains(route=f"event/{season}{event}/matches/simple") and cache_enabled and not refresh_cache:
        j = ba_cache.uncache("route", f"event/{season}{event}/matches/simple", "data")
    else:
        resp = request_session.get(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/matches/simple")
        if resp.status_code == 401:
            return abort(401)
        j = resp.json()
        if cache_enabled:
            ba_cache.cache("route", f"event/{season}{event}/matches/simple", "data", j)
    return {e['key'].split("_")[-1]: e['key'] for e in j}

@bp.route('/<season>/<event>/<match>/', methods=("GET",))
def match_info(season, event, match):
    ba_cache = db.get_connector().create_simple("blueallianceCache")
    matchCode = season+event+"_"+match
    cache_enabled = request.args.get("cache", "true") == "true"
    refresh_cache = request.args.get("refresh", "false") == "true"
    if ba_cache.contains(route=f"match/{matchCode}/simple") and cache_enabled and refresh_cache:
        j = ba_cache.uncache("route", f"match/{matchCode}/simple", "data")
    else:
        resp = request_session.get(f"https://www.thebluealliance.com/api/v3/match/{matchCode}/simple")
        if resp.status_code == 401:
            return abort(401)
        j = resp.json()
        if 'Error' in j:
            return abort(Response(j['Error'], 401))
        if cache_enabled:
            ba_cache.cache("route", f"match/{matchCode}/simple", "data", j)
    a = j['alliances']
    o = {}
    for alliance in a.keys():
        for teamCode in a[alliance]['team_keys']:
            o[teamCode[3:]] = alliance
    return o
