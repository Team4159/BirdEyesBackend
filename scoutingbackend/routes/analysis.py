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
        self.rest.add_resource(self.AutoScoring, '/2023/<string:event>/<integer:team>/autoScoring')
    
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

            single_total = double_total = 0

            for row in matches:
                single_total += int(row["teleopIntakessingle"])
                double_total += int(row["teleopIntakesdouble"])

            return { "singlePercentage": single_total / len(matches), "doublePercentage": double_total / len(matches) }
        
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

            score_total = 0

            for row in matches:
                for key in self.SCORING_POINTS.keys():
                    score_total += int(row[key]) * self.SCORING_POINTS[key]

            return { "score": score_total / len(matches) }
    
    class AutoScoring(flask_restful.Resource):
        AUTO_SCORING_POINTS = { # Might move elsewhere
            "low"   : 3,
            "mid"   : 4,
            "high"  : 6,
            "mobility"  : 3,
            "docked"    : 8,
            "engaged"   : 4,
        }

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