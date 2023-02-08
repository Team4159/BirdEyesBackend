import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort, Response
)

from . import db

bp = Blueprint('api', __name__, url_prefix='/api')

SCHEMAS = {
    '2023': '''{
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
        }'''
}

@bp.route('/test', methods=("GET",))
def test():
    return f"its flasking time {request.args.get('argument', '')}"

@bp.route('/nottest', methods=("GET",))
def nottest():
    return "idk"


@bp.route('/createChargedUpEvent', methods=("POST",))
def ChargedUpEventCreate():
    event = request.args.get("eventName", None)
    if event is None:
        return abort(400)
    c = db.get_db()
    db.create_chargedup_event("_"+event)
    return Response("table created", 200)

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

@bp.route('/<event>/', methods=("GET",))
def eventschema(event=None):
    if event not in SCHEMAS:
        return abort(404)
    return SCHEMAS[event]

@bp.route('/<event>/match/', methods=('POST', 'GET'))
def match(event=None):
    if event is None:
        return abort(500)
    if request.method == "POST":
        j = request.get_json()
        c = db.get_db()
        c.execute(f"INSERT INTO _{event}_match VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            j['qual'], j['teamNumber'],
            j['auto']['coneAttempted'], j['auto']['coneLow'], j['auto']['coneMid'], j['auto']['coneHig'], int(j['auto']['mobility']),
            j['teleop']['coneAttempted'], j['teleop']['coneLow'], j['teleop']['coneMid'], j['teleop']['coneHig'],
            int(j['endgame']['docked']), int(j['endgame']['engaged']),
            j['driver']['rating'], j['driver']['fouls']
        ))
        c.commit()
        return Response(f"successfully added response (qual {j['qual']} team {j['teamNumber']})", 200)

    elif request.method == "GET":
        j = {
            'auto':{},
            'teleop':{},
            'endgame':{},
            'driver':{}
        }
        c = db.get_db()
        vals = c.execute(f"SELECT * FROM _{event}_match WHERE qual=? AND teamNumber=?", (request.args.get('qual'), request.args.get('teamNumber'))).fetchone()
        if not vals:
            return abort(404)
        j['qual'], j['teamNumber'], j['auto']['coneAttempted'], j['auto']['coneLow'], j['auto']['coneMid'], j['auto']['coneHig'], j['auto']['mobility'], \
            j['teleop']['coneAttempted'], j['teleop']['coneLow'], j['teleop']['coneMid'], j['teleop']['coneHig'], \
            j['endgame']['docked'], j['endgame']['engaged'], \
            j['driver']['rating'], j['driver']['fouls'] = vals
        print(j)
        return j
