import sqlite3

from flask import Blueprint, Response, abort, request
from flask_cors import cross_origin

from scoutingbackend.schemes import *

from . import db

bp = Blueprint('api', __name__, url_prefix='/api')

def format_event(season: int, event_id: str):
    return f"frc{season}{event_id}"

@bp.route('/<season>/createEvent', methods=("PUT",))
def createEvent(season):
    if season not in MATCH_SCHEME or season not in PIT_SCHEME or request.data == None:
        return abort(Response("Unrecognized Season / Bad Data", 400))
    c = db.get_db()
    c.executescript(DB_SCHEME[season].format(event=format_event(season, request.data.decode())))
    c.commit()
    return Response("Table Created / Already Exists", 200)

@bp.route('/<season>/matchschema/', methods=("GET",))
@cross_origin()
def eventmatchschema(season):
    return MATCH_SCHEME[season] if season in MATCH_SCHEME else abort(404)

@bp.route('/<season>/pitschema/', methods=("GET",))
@cross_origin()
def eventpitschema(season):
    return PIT_SCHEME[season] if season in PIT_SCHEME else abort(404)

@bp.route('/<season>/<event>/pit/', methods=('POST', 'GET',))
@cross_origin()
def pit(season, event):
    eventCode = format_event(season, event)
    c = db.get_db()
    if request.method == "POST":
        j = request.get_json(force=True)
        try:
            c.execute(f"INSERT INTO {eventCode}_pit ( %s ) VALUES ( %s )" % (', '.join(PIT_SCHEME[season].values())+', teamNumber', ', '.join(['%s'] * len(j))), list(j.values()))
        except sqlite3.OperationalError:
            return abort(404)
        c.commit()
        return Response(f"Successfully Added Pit Response! ({j['teamNumber']})", 200)
    elif request.method == "GET":
        j = {}
        try:
            vals = c.execute(f'SELECT * FROM {eventCode}_pit' + (" WHERE teamNumber="+request.args.get('teamNumber') if "teamNumber" in request.args else "")).fetchone()
        except sqlite3.OperationalError:
            return abort(Response("SQL Operational Error", 404))
        if vals == None:
            return abort(404)
        j['teamNumber'], j['response'] = vals
        print(j)
        return j

@bp.route('/<event>/match/', methods=('POST', 'GET'))
@cross_origin()
def match(event):
    event = format_event(event)
    if request.method == "POST":
        j = request.get_json()
        c = db.get_db()
        try:
            c.execute(f"INSERT INTO {event}_match VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                j['qual'], j['teamNumber'],
                j['auto']['coneAttempted'], j['auto']['coneLow'], j['auto']['coneMid'], j['auto']['coneHig'], int(j['auto']['mobility']),
                j['teleop']['coneAttempted'], j['teleop']['coneLow'], j['teleop']['coneMid'], j['teleop']['coneHig'],
                int(j['endgame']['docked']), int(j['endgame']['engaged']),
                j['driver']['rating'], j['driver']['fouls']
            ))
        except sqlite3.OperationalError:
            return abort(404)
        c.commit()
        return Response(f"successfully added match response (qual {j['qual']} team {j['teamNumber']})", 200)

    elif request.method == "GET":
        if not (request.args.get('qual', None) and request.args.get('teamNumber', None)):
            return abort(400)
        j = {
            'auto':{},
            'teleop':{},
            'endgame':{},
            'driver':{}
        }
        c = db.get_db()
        try:
            vals = c.execute(f"SELECT * FROM {event}_match WHERE qual=? AND teamNumber=?", (request.args.get('qual'), request.args.get('teamNumber'))).fetchone()
        except sqlite3.OperationalError:
            return abort(404)
        if not vals:
            return abort(404)
        j['qual'], j['teamNumber'], j['auto']['coneAttempted'], j['auto']['coneLow'], j['auto']['coneMid'], j['auto']['coneHig'], j['auto']['mobility'], \
            j['teleop']['coneAttempted'], j['teleop']['coneLow'], j['teleop']['coneMid'], j['teleop']['coneHig'], \
            j['endgame']['docked'], j['endgame']['engaged'], \
            j['driver']['rating'], j['driver']['fouls'] = vals
        print(j)
        return j
