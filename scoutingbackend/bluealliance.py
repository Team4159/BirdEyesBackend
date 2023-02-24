import json
import os
from flask import Blueprint, Response, abort

bp = Blueprint('bluealliance', __name__, url_prefix='/bluealliance')

def init_cache(app):
    global season, event, matches, teams
    with app.app_context():
        jo = json.load(open(os.path.join(app.instance_path, 'cache.json'), "r"))
        if "season" not in jo or "event" not in jo or "matches" not in jo or "teams" not in jo:
            raise Exception("Malformed JSON Cache")
        season = jo["season"]
        event = jo["event"]
        matches = jo["matches"]
        teams = jo["teams"]

@bp.route("/", methods=("GET",))
def current_seasons():
    return {"max_season": season, "current_season": season}

@bp.route('/<season>/', methods=("GET",))
def current_events(season):
    if (season != str(season)): return abort(Response("Response Not Cached", 404))
    return {event: "Cached Event"}

@bp.route('/<season>/<event>/', methods=("GET",))
def current_matches(season, event):
    if (season != str(season) or event != event): return abort(Response("Response Not Cached", 404))
    return matches

@bp.route('/<season>/<event>/<match>/', methods=("GET",))
def match_info(season, event, match):
    if (season != str(season) or event != event or match not in teams): return abort(Response("Response Not Cached", 404))
    return teams[match]
