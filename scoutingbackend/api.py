import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort, Response
)

from . import db

bp = Blueprint('api', __name__, url_prefix='/api')

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
    db.create_chargedup_event(event)
    return Response("table created", 200)

@bp.route('/submitMatchResponse', methods = ("POST",))
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

@bp.route('/match/', methods=('POST', 'GET'))
def match():
    pass
