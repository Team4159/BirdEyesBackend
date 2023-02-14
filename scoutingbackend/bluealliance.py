import os
from datetime import date, datetime

from flask import Blueprint, abort, request
from requests import Session

request_session = Session()
request_session.headers['X-TBA-Auth-Key'] = os.getenv('TBA_KEY')

bp = Blueprint('bluealliance', __name__, url_prefix='/bluealliance')

def is_valid_event(event: dict, ignore_date=False):
    start_date = datetime.strptime(event['start_date'], r"%Y-%m-%d",).date()
    end_date = datetime.strptime(event['end_date'], r"%Y-%m-%d").date()
    today = date.today()
    return event['state_prov'] == os.getenv('TBA_STATE') and (ignore_date or start_date <= today <= end_date)

@bp.route('/currentEvents/')
def current_events():    
    resp = request_session.get(f"https://www.thebluealliance.com/api/v3/events/{os.getenv('SEASON')}/simple")
    if resp.status_code == 401:
        return abort(401)
    event_list = filter(lambda b: is_valid_event(b, request.args.get('ignoreDate', False)), resp.json())
    return {e['event_code']: e['name'] for e in event_list}

@bp.route('/updateAll')
def update_all():
    pass

@bp.route('/<event>/<qual>/updateLocal')
def update_match_info(event, qual):
    pass
