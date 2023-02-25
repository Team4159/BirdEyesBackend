import json
import os
from flask import Blueprint, Response, abort

bp = Blueprint('bluealliance', __name__, url_prefix='/bluealliance')

def init_cache(app):
    global _season, _event, _matches, _teams
    with app.app_context():
        jo = json.load(open(os.path.join(app.instance_path, 'cache.json'), "r"))
        if "season" not in jo or "event" not in jo or "matches" not in jo or "teams" not in jo:
            raise Exception("Malformed JSON Cache")
        _season = jo["season"]
        _event = jo["event"]
        _matches = jo["matches"]
        _teams = jo["teams"]
        _teams["*"] = {}
        for vo in _teams.values():
            for k in vo.keys():
                _teams["*"][k] = "*"

@bp.route("/", methods=("GET",))
def current_seasons():
    return {"max_season": _season, "current_season": _season}

@bp.route('/<season>/', methods=("GET",))
def current_events(season):
    if (season != str(_season)): return abort(Response("Response Not Cached", 404))
    return {_event: "Cached Event"}

@bp.route('/<season>/<event>/', methods=("GET",))
def current_matches(season, event):
    if (season != str(_season) or event != _event): return abort(Response("Response Not Cached", 404))
    return _matches

@bp.route('/<season>/<event>/<match>/', methods=("GET",))
def match_info(season, event, match):
    if (season != str(_season) or event != _event or match not in _teams): return abort(Response("Response Not Cached", 404))
    return _teams[match]
