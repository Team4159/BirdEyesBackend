import functools
import sqlite3
from flask_cors import CORS, cross_origin

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort, Response
)

from . import db

bp = Blueprint('api', __name__, url_prefix='/api')

PIT_SCHEME = {
    '2023': {
        "dfe": "text",
        "AMONG US": "text",
    }
}

MATCH_SCHEME = {
    '2023': {
        "auto": {
        "coneAttempted": "counter",
        "coneLow": "counter",
        "coneMid": "counter",
        "coneHig": "counter",
        "mobility":"toggle"
        },
        "teleop": {
        "coneAttempted": "counter",
        "coneLow": "counter",
        "coneMid": "counter",
        "coneHig": "counter"
        },
        "endgame": {
        "docked": "toggle",
        "engaged":"toggle"
        },
        "driver": {
        "rating": "slider",
        "fouls": "counter"
        }
    }
}

DB_SCHEME = {
    "2023": """CREATE TABLE IF NOT EXISTS {event}_match (
        qual TEXT NOT NULL,
        teamNumber INTEGER NOT NULL,

        autoConeAttempt INTEGER,
        autoConeLow INTEGER,
        autoConeMid INTEGER,
        autoConeHigh INTEGER,
        autoMobility INTEGER,
        teleopConeAttempt INTEGER,
        teleopConeLow INTEGER,
        teleopConeMid INTEGER,
        teleopCodeHigh INTEGER,
        endgameDock INTEGER,
        endgameEngage INTEGER,
        driverRating INTEGER,
        driverFouls INTEGER,

        PRIMARY KEY (qual, teamNumber)
    );
    CREATE TABLE IF NOT EXISTS {event}_pit (
        teamNumber INTEGER PRIMARY KEY NOT NULL,
        response TEXT
    );
    """
}

@bp.route('/test', methods=("GET",))
@cross_origin()
def test():
    return f"its flasking time {request.args.get('argument', '')}"

@bp.route('/nottest', methods=("GET",))
@cross_origin()
def nottest():
    return "idk"

'''@bp.route('/submitMatchResponse', methods = ("POST",))
def submit_match_response():
    resp = request.get_json()
    event: str = resp['event']
    qual: str = resp['qual']
    team_number: int = resp['teamNumber']
    points: int = resp['points']
    ranking_points = resp['rankingPoints']

    c = db.get_db()
    c.execute(f"INSERT INTO {event} (qual, teamNumber, points, rankingPoints) VALUES (?, ?, ?, ?)", (qual, team_number, points, ranking_points))
    return Response(f"successfully added response (qual {qual} team {team_number})", 200)
'''

def format_event(event_id: str):
    return f"frc{event_id}"

@bp.route('/<event>/create', methods=("POST",))
@cross_origin()
def create(event):
    event = format_event(event)
    if not request.args.get('year', None):
        return abort(400)
    c = db.get_db()
    c.executescript(DB_SCHEME[request.args.get('year')].format(event=event))
    c.commit()
    return Response("table created/table already exists", 200)

@bp.route('/<season>/matchschema/', methods=("GET",))
@cross_origin()
def eventmatchschema(season):
    if season not in MATCH_SCHEME:
        return abort(404)
    print(MATCH_SCHEME[season])
    return MATCH_SCHEME[season]

@bp.route('/<season>/pitschema/', methods=("GET",))
@cross_origin()
def eventpitschema(season):
    if season not in PIT_SCHEME:
        return abort(404)
    print(PIT_SCHEME[season])
    return PIT_SCHEME[season]

@bp.route('/<event>/pit/', methods=('POST', 'GET'))
@cross_origin()
def pit(event):
    event = format_event(event)
    if request.method == "POST":
        j = request.get_json()
        c = db.get_db()
        try:
            c.execute(f"INSERT INTO {event}_pit (teamNumber, response) VALUES (?, ?)", (j['teamNumber'], j['response']))
        except sqlite3.OperationalError:
            return abort(404)
        c.commit()
        return Response(f"successfully added pit response (qual {j['qual']} team {j['teamNumber']})", 200)
    elif request.method == "GET":
        if not request.args.get("teamNumber", None):
            return abort(400)
        j = {}
        c = db.get_db()
        try:
            vals = c.execute(f'SELECT * FROM {event}_pit WHERE teamNumber=?', (request.args.get('teamNumber'),)).fetchone()
        except sqlite3.OperationalError:
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
