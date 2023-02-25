import json
import sqlite3

from flask import Blueprint, Response, abort, request

from scoutingbackend.schemes import MATCH_SCHEME, PIT_SCHEME, format_event

from . import bluealliance, db

bp = Blueprint('api', __name__, url_prefix='/api')
bp.register_blueprint(bluealliance.bp)

@bp.route('/<season>/listEvents/', methods=('GET',))
def get_season_events(season):
    tablenames = db.get_db().execute("SELECT name from sqlite_master WHERE type='table'").fetchall()
    tablenames = [e['name'] for e in tablenames if e['name'].startswith(f'frc{season}')]
    return json.dumps(tablenames)

@bp.route('/<season>/createEvent/', methods=("PUT",))
def create_event(season):
    if season not in MATCH_SCHEME or season not in PIT_SCHEME or request.data == None:
        return abort(Response("Unrecognized Season / Bad Data", 400))
    c = db.get_db()
    c.executescript(db.DB_SCHEME[season].format(event=format_event(season, request.data.decode())))
    c.commit()
    return Response("Table Created / Already Exists", 200)

@bp.route('/<season>/matchschema/', methods=("GET",))
def eventmatchschema(season):
    return Response(json.dumps(MATCH_SCHEME[season], sort_keys=False), 200, content_type='application/json') if season in MATCH_SCHEME else abort(404)

@bp.route('/<season>/pitschema/', methods=("GET",))
def pit_schema(season):
    return PIT_SCHEME[season] if season in PIT_SCHEME else abort(404)

@bp.route('/<season>/<event>/pit/', methods=('POST', 'GET',))
def pit(season, event):
    eventCode = format_event(season, event)
    c = db.get_db()
    if request.method == "POST":
        j = request.get_json(force=True)
        try:
            if j["teamNumber"] is None or j["name"] is None:
                return abort(Response("Missing Required Fields", 400))
            c.execute(f"INSERT INTO {eventCode}_pit ( {', '.join(j.keys())} ) VALUES ( {', '.join(['?'] * len(j))} )", list(j.values()))
        except sqlite3.OperationalError as e:
            return abort(Response(e, 500))
        c.commit()
        return Response(f"Successfully Added Pit Response! (#{j['teamNumber']})", 200)
    elif request.method == "GET":
        try:
            vals = c.execute(f"SELECT * FROM {eventCode}_pit " + db.generate_selector(request.args))
        except sqlite3.OperationalError as e:
            return abort(Response(e, 500))
        if not vals:
            return abort(404)
        return [dict(v) for v in vals]

@bp.route('/<season>/<event>/match/', methods=('POST', 'GET',))
def match(season, event):
    eventCode = format_event(season, event)
    c = db.get_db()
    if request.method == "POST":
        j = request.get_json(force=True)
        try:
            if j["teamNumber"] is None or j["match"] is None or j["name"] is None or j["form"] is None:
                return abort(Response("Missing Required Fields", 400))
            jp = {}
            for k, v in j["form"].items():
                for k1, v1 in v.items():
                    jp[k+k1[0].upper()+k1[1:]] = v1
            jp["teamNumber"] = j["teamNumber"]
            jp["match"] = j["match"]
            jp['name'] = j['name']

            c.execute(f"INSERT INTO {eventCode}_match ( {', '.join(jp.keys())} ) VALUES ( {', '.join(['?'] * len(jp))} )", list(jp.values()))
        except sqlite3.OperationalError as e:
            print(e)
            return abort(Response(str(e), 500))
        c.commit()
        return Response(f"Successfully Added Match Response! (#{jp['teamNumber']} @ {jp['match']})", 200)
    elif request.method == "GET":
        try:
            vals = c.execute(f"SELECT * FROM {eventCode}_match "+db.generate_selector(request.args))
        except sqlite3.OperationalError as e:
            return abort(Response(str(e), 500))
        if not vals:
            return abort(404)
        return [dict(v) for v in vals]