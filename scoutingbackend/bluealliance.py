import sqlite3
import requests
import os
import datetime

from flask import (Blueprint, Response, abort, flash, g, redirect,
                   render_template, request, session, url_for)
from flask_cors import CORS, cross_origin

from . import db

request_session = requests.Session()
request_session.headers['X-TBA-Auth-Key'] = os.getenv("TBA_KEY")

bp = Blueprint('bluealliance', __name__, url_prefix='/bluealliance')

@bp.route('/updateAll')
def update_all():
    pass

def is_valid_event(event: dict, ignore_date=False):
    start_date = datetime.datetime.strptime(event['start_date'], r"%Y-%m-%d",).date()
    end_date = datetime.datetime.strptime(event['end_date'], r"%Y-%m-%d").date()
    today = datetime.date.today()
    return event['state_prov'] == os.getenv('TBA_STATE') and (ignore_date or start_date <= today <= end_date)

@bp.route('/getCurrentEvents')
def get_current_events():
    resp = request_session.get(f"https://www.thebluealliance.com/api/v3/events/{datetime.date.today().year}/simple")
    if resp.status_code == 401:
        return abort(401)
    event_list = resp.json()
    if request.args.get('anyDate'):
        event_list = filter(lambda b: is_valid_event(b, True), event_list)
    else:
        event_list = filter(is_valid_event, event_list)
    print(event_list)
    return {e['event_code']: e['name'] for e in event_list}

@bp.route('/<event>/<qual>/updateLocal')
def update_match_info(event, qual):
    pass

