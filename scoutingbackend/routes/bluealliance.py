import datetime
import typing

import flask
import flask_restful

from scoutingbackend.cachingsession import get_with_cache, session
from scoutingbackend.database import db
from scoutingbackend.restfulerror import RestfulErrorApi


class BlueAlliance(object):
    def __init__(self, api_key: str) -> None:
        session.headers['X-TBA-Auth-Key'] = api_key
        self.bp = flask.Blueprint('ba', __name__, url_prefix='/bluealliance')
        
        self.rest = RestfulErrorApi(self.bp)
        self.rest.add_resource(self.BAIndex, '/')
        self.rest.add_resource(self.BASeason, '/<int:season>')
        self.rest.add_resource(self.BAEvent, '/<int:season>/<string:event>')
        self.rest.add_resource(self.BAMatch, '/<int:season>/<string:event>/<string:match>')

        self.index = self.BAIndex()
        self.season= self.BASeason()
        self.event = self.BAEvent()
        self.match = self.BAMatch()
        
    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)
    
    @staticmethod
    def is_valid_event(event: dict, ignore_date=False):
        start_date = datetime.datetime.strptime(event['start_date'], r"%Y-%m-%d",).date()
        end_date = datetime.datetime.strptime(event['end_date'], r"%Y-%m-%d").date()
        today = datetime.date.today()
        return ("TBA_STATE" not in flask.current_app.config or event['state_prov'] == flask.current_app.config['TBA_STATE']) and (ignore_date or start_date <= today <= end_date)
    
    class BAIndex(flask_restful.Resource):
        def get(self):
            resp = get_with_cache("https://www.thebluealliance.com/api/v3/status")
            if not resp.ok:
                return flask_restful.abort(resp.status_code, description="Error getting status of TheBlueAlliance", details=resp.content.decode(resp.encoding if resp.encoding else 'utf8'))
            j = resp.json()
            return {"max_season": j['max_season'], "current_season": j['current_season']}
            
    class BASeason(flask_restful.Resource):
        def get(self, season: int):
            resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/events/{season}/simple")
            if not resp.ok:
                return flask_restful.abort(resp.status_code, description="Error getting season data from TheBlueAlliance", details=resp.content.decode(resp.encoding if resp.encoding else 'utf8'))
            j = resp.json()
            return {e['event_code']: e['name'] for e in j if BlueAlliance.is_valid_event(e, flask.request.args.get('ignoreDate', "false")=="true")}
    
    class BAEvent(flask_restful.Resource):
        def get(self, season: int, event: str):
            resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/matches/simple")
            if not resp.ok:
                return flask_restful.abort(resp.status_code, description="Error getting match data from TheBlueAlliance", details=resp.content.decode(resp.encoding if resp.encoding else 'utf8'))
            j = resp.json()
            return {e['key'].split("_")[-1]: e['key'] for e in j}
        
    class BAMatch(flask_restful.Resource):
        def get(self, season: int, event: str, match: str):
            if match == "*":
                resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/event/{season}{event}/teams/keys")
                if not resp.ok:
                    return flask_restful.abort(resp.status_code, description="Error getting match data from TheBlueAlliance (request 1/2)", details=resp.content.decode(resp.encoding if resp.encoding else 'utf8'))
                if flask.request.args.get("onlyUnfilled", "false") == "true":
                    try:
                        scoutedlist = [t['teamNumber'] for t in db.connection().cursor().execute(f"SELECT (teamNumber) FROM frc{season}{event}_pit").fetchall()]
                    except:
                        scoutedlist = []
                    full_list = [int(team_code[3:]) for team_code in resp.json() if int(team_code[3:]) != 0]
                    return list(set(full_list).difference(scoutedlist))
                else:
                    return {team_code[3:]: "*" for team_code in resp.json()}
            resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/match/{season}{event}_{match}/simple")
            if not resp.ok:
                return flask_restful.abort(resp.status_code, description="Error getting match data from TheBlueAlliance (request 2/2)", details=resp.content.decode(resp.encoding if resp.encoding else 'utf8'))
            j = resp.json()
            if 'Error' in j:
                return flask_restful.abort(401, description=j['Error'], details=resp.content.decode(resp.encoding if resp.encoding else 'utf8'))
            o = {}
            for alliance, allianceData in j['alliances'].items():
                for num, teamCode in enumerate(allianceData['team_keys']):
                    if teamCode[3:] != "0":
                        o[teamCode[3:]] = alliance+str(num+1)
            return o