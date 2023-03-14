import typing

import flask
import flask_restful

from scoutingbackend.cachingsession import get_with_cache
from scoutingbackend.database import db
from scoutingbackend.schemes import invert_alliance


class Analysis2023(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('an', __name__, url_prefix='/analysis/2023')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.BestDefense, '/<string:event>/bestDefense')
        self.rest.add_resource(self.BestScoring, '/<string:event>/bestScoring')
        self.rest.add_resource(self.BestAuto   , '/<string:event>/bestAuto'   )
        self.rest.add_resource(self.PickupLocations, '/<string:event>/pickups')

        self.rest.add_resource(self.AutoScoring, '/<string:event>/<int:team>/autoScoring')

    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)

    class BestDefense(flask_restful.Resource):
        def get(self, event: str):
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> float:
                netscore = 0
                total = 0
                for row in c.execute(f"select * from {table} where teamNumber={team}").fetchall():
                    resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/match/2023{event}_{row['match']}")
                    if not resp.ok:
                        raise Exception(f"[Analysis] Request Error. "+resp.text)
                    matchinfo = resp.json()
                    alliance = [a for a in matchinfo["alliances"] if f"frc{row['teamNumber']}" in matchinfo["alliances"][a]["team_keys"]]
                    if len(alliance) != 1:
                        raise Exception(f"[Analysis] Invalid Alliance. Team: {row['teamNumber']} @ Match: {row['match']}")
                    alliance = alliance[0]
                    driverskill = row["commentsDriverrating"]/(5*(row["commentsFouls"]+1)*(0.7 if row["commentsDefensive"] == 1 else 1))
                    defensescore= matchinfo["score_breakdown"][alliance]["foulPoints"]-matchinfo["score_breakdown"][invert_alliance[alliance]]["teleopPoints"]
                    netscore += driverskill*defensescore
                    total += 1
                return netscore/total
            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            return dict(sorted(teams.items(), key=lambda item: item[1]))
    
    class BestScoring(flask_restful.Resource):
        def get(self, event: str):
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> float:
                netscore = 0
                total = 0
                for row in c.execute(f"select * from {table} where teamNumber={team}").fetchall():
                    resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/match/2023{event}_{row['match']}")
                    if not resp.ok:
                        raise Exception(f"[Analysis] Request Error. "+resp.text)
                    matchinfo = resp.json()
                    alliance = [a for a in matchinfo["alliances"] if f"frc{row['teamNumber']}" in matchinfo["alliances"][a]["team_keys"]]
                    if len(alliance) != 1:
                        raise Exception(f"[Analysis] Invalid Alliance. Team: {row['teamNumber']} @ Match: {row['match']}")
                    alliance = alliance[0]
                    netscore += 3*total_points(row)/matchinfo["score_breakdown"][alliance]["totalPoints"]
                    total += 1
                return netscore/total
            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            return dict(sorted(teams.items(), key=lambda item: item[1]))
    
    class BestAuto(flask_restful.Resource):
        def get(self, event: str):
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> float:
                netscore = 0
                total = 0
                for row in c.execute(f"select * from {table} where teamNumber={team}").fetchall():
                    resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/match/2023{event}_{row['match']}")
                    if not resp.ok:
                        raise Exception(f"[Analysis] Request Error. "+resp.text)
                    matchinfo = resp.json()
                    alliance = [a for a in matchinfo["alliances"] if f"frc{row['teamNumber']}" in matchinfo["alliances"][a]["team_keys"]]
                    if len(alliance) != 1:
                        raise Exception(f"[Analysis] Invalid Alliance. Team: {row['teamNumber']} @ Match: {row['match']}")
                    alliance = alliance[0]
                    netscore += 3*auto_points(row)/matchinfo["score_breakdown"][alliance]["autoPoints"]
                    total += 1
                return netscore/total
            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            return dict(sorted(teams.items(), key=lambda item: item[1]))
    
    class PickupLocations(flask_restful.Resource):
        def get(self, event: str, team: int):
            single = {}
            double = {}
            for row in db.connection().cursor().execute(f"select * from frc2023{event}_match where teamNumber={team}").fetchall():
                tn = row["teamNumber"]
                if tn not in single: single[tn] = 0
                if tn not in double: double[tn] = 0
                if row["teleopIntakessingle"]: single[tn]+=1
                if row["teleopIntakesdouble"]: double[tn]+=1
            return {
                "single": [t for t in single.keys() if single[t] > double[t]*1.5],
                "double": [t for t in double.keys() if double[t] > single[t]*1.5],
                "both": [t for t in set(single.keys()).intersection(double.keys()) if single[t] <= double[t]*1.5 and double[t] <= single[t]*1.5]
            }
    
    class AutoScoring(flask_restful.Resource):
        def get(self, event: str, team: int):
            cursor = db.connection().cursor()
            table = f"frc2023{event}_match"
            matches = cursor.execute(f"select * from {table} where teamNumber={team}").fetchall()

            cone_low_total = cone_mid_total = cone_high_total = cone_percentage_total = cube_low_total = cube_mid_total = cube_high_total = cube_percentage_total = score_total = 0

            for row in matches:
                cone_low_total += row["autoConelow"]
                cone_mid_total += row["autoConemid"]
                cone_high_total += row["autoConehigh"]
                cone_percentage_total += (row["autoConelow"] + row["autoConemid"] + row["autoConehigh"]) / (row["autoConeAttempts"] + row["autoConelow"] + row["autoConemid"] + row["autoConehigh"])
                cube_low_total += row["autoCubelow"]
                cube_mid_total += row["autoCubemid"]
                cube_high_total += row["autoCubehigh"]
                cube_percentage_total += (row["autoCubelow"] + row["autoCubemid"] + row["autoCubehigh"]) / (row["autoCubeAttempts"] + row["autoCubelow"] + row["autoCubemid"] + row["autoCubehigh"])
                score_total += int(row["autoMobility"]) * self.AUTO_SCORING_POINTS["mobility"] + int(row["autoDocked"]) * self.AUTO_SCORING_POINTS["docked"] + int(row["autoEngaged"]) * self.AUTO_SCORING_POINTS["engaged"]
            
            score_total += (cone_low_total + cube_low_total) * self.AUTO_SCORING_POINTS["low"] + (cone_mid_total + cube_high_total) * self.AUTO_SCORING_POINTS["mid"] + (cone_high_total + cube_high_total) * self.AUTO_SCORING_POINTS["high"]

            return {
                "averageConeLow": cone_low_total / len(matches),
                "averageConeMid": cone_mid_total / len(matches),
                "averageConeHigh": cone_high_total / len(matches),
                "conePercentage": cone_percentage_total / len(matches),
                "averageCubeLow": cube_low_total / len(matches),
                "averageCubeMid": cube_mid_total / len(matches),
                "averageCubeHigh": cube_high_total / len(matches),
                "cubePercentage": cube_percentage_total / len(matches),
                "averageScore": score_total / len(matches),
            }

SCORING_POINTS = {
    "autoConeLow"   : 3,
    "autoConeMid"   : 4,
    "autoConeHigh"  : 6,
    "autoCubeLow"   : 3,
    "autoCubeMid"   : 4,
    "autoCubeHigh"  : 6,
    "autoMobility"  : 3,
    "autoDocked"    : 8,
    "autoEngaged"   : 4,
    "teleopConeLow" : 2,
    "teleopConeMid" : 3,
    "teleopConeHigh": 5,
    "teleopCubeLow" : 2,
    "teleopCubeMid" : 3,
    "teleopCubeHigh": 5,
    "endgameParked" : 2,
    "endgameDocked" : 6,
    "endgameEngaged": 4,
}
def total_points(row):
    return sum([SCORING_POINTS[k] for k in row.keys()])
def auto_points(row):
    return sum([SCORING_POINTS[k] for k in row.keys() if k.startswith("auto")])