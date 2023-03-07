import typing

import flask
import flask_restful

from scoutingbackend.cachingsession import get_with_cache
from scoutingbackend.database import db
from scoutingbackend.schemes import invert_alliance


class Analysis2023(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('an', __name__, url_prefix='/analysis')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.BestDefense, '/2023/<string:event>/bestDefense')
        self.rest.add_resource(self.BestOffense, '/2023/<string:event>/bestOffense')
        self.rest.add_resource(self.BestAuto, '/2023/<string:event>/bestAuto')
        self.rest.add_resource(self.PickupLocations, '/2023/<string:event>/<integer:team>/pickup')
        self.rest.add_resource(self.AveragePointsPerGame, '/2023/<string:event>/<integer:team>/points')
    
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
    
    class BestOffense(flask_restful.Resource):
        def get(self, event: str):
            # c = db.connection().cursor()
            # table = f"frc2023{event}_match"
            # def k(team: str) -> float:
            #     netscore = 0
            #     total = 0
            #     for row in c.execute(f"select * from {table} where teamNumber={team}").fetchall():
            #         resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/match/2023{event}_{row['match']}")
            #         if not resp.ok:
            #             raise Exception(f"[Analysis] Request Error. "+resp.text)
            #         matchinfo = resp.json()
            #         alliance = [a for a in matchinfo["alliances"] if f"frc{row['teamNumber']}" in matchinfo["alliances"][a]["team_keys"]]
            #         if len(alliance) != 1:
            #             raise Exception(f"[Analysis] Invalid Alliance. Team: {row['teamNumber']} @ Match: {row['match']}")
            #         alliance = alliance[0]
            #         driverskill = row["commentsDriverrating"]/(5*(row["commentsFouls"]+1)*(0.7 if row["commentsDefensive"] == 1 else 1))
            #         3*total_score(row)/matchinfo["teleopPoints"]
            #         netscore += driverskill*defensescore
            #         total += 1
            #     return netscore/total
            return {}
    
    class BestAuto(flask_restful.Resource):
        def get(self, event: str):
            return {}
    
    class PickupLocations(flask_restful.Resource):
        def get(self, event: str, team: int):
            cursor = db.connection().cursor()
            table = f"frc2023{event}_match"
            matches = cursor.execute(f"select * from {table} where teamNumber={team}").fetchall()

            singleTotal = 0
            doubleTotal = 0

            for row in matches:
                singleTotal += int(row["teleopIntakessingle"])
                doubleTotal += int(row["teleopIntakesdouble"])

            return { "singlePercentage": singleTotal / len(matches), "doublePercentage": doubleTotal / len(matches) }
        
    class AveragePointsPerGame(flask_restful.Resource):
        SCORING_POINTS = { # Might move elsewhere
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

        def get(self, event: str, team: int):
            cursor = db.connection().cursor()
            table = f"frc2023{event}_match"
            matches = cursor.execute(f"select * from {table} where teamNumber={team}").fetchall()

            score = 0

            for row in matches:
                for key in self.SCORING_POINTS.keys():
                    score += int(row[key]) * self.SCORING_POINTS[key]

            return { "points": score / len(matches) }