import csv
import io
import sqlite3
import typing
from collections import OrderedDict

import flask
import flask_restful

from scoutingbackend.cachingsession import get_with_cache
from scoutingbackend.database import db
from scoutingbackend.schemes import invert_alliance
from scoutingbackend.restfulerror import RestfulErrorApi

def special_divide(n, d):
    return n/d if d else 0

class Analysis2023(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('an', __name__, url_prefix='/analysis/2023')
        self.rest = RestfulErrorApi(self.bp)
        self.rest.add_resource(self.BestDefense, '/<string:event>/bestDefense')
        self.rest.add_resource(self.BestScoring, '/<string:event>/bestScoring')
        self.rest.add_resource(self.BestAuto   , '/<string:event>/bestAuto'   )
        self.rest.add_resource(self.BestTeleop , '/<string:event>/bestTeleop' )
        self.rest.add_resource(self.BestEndgame, '/<string:event>/bestEndgame')

        self.rest.add_resource(self.PickupLocations, '/<string:event>/pickups')
        self.rest.add_resource(self.AutoScoring, '/<string:event>/<int:team>/autoScoring')
        self.rest.add_resource(self.SaturatedEvent, '/<string:event>')

    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)
    
    @staticmethod
    def ranking_wrapper(event: str, key: typing.Optional[str], friendly_key: typing.Optional[str] = None):
        c = db.connection().cursor()
        c.row_factory = lambda cur, row: row[0]
        team_scores_unsorted = {int(team): Analysis2023.get_point_values(event, team, key) for team in set(c.execute(f"select (teamNumber) from frc2023{event}_match").fetchall())} #set to remove dupes
        c.row_factory = sqlite3.Row #type:ignore
        team_scores = OrderedDict(sorted(team_scores_unsorted.items(), key=lambda teaminfo: teaminfo[1], reverse=True))
        if flask.request.args.get("csv", "false") == "false":
            return team_scores
        else:
            out = io.StringIO()
            friendly_name = f"Average Score ({key})" if not friendly_key else friendly_key
            writer = csv.DictWriter(out, fieldnames=["Team Number", friendly_name])
            writer.writeheader()
            writer.writerows([{"Team Number": team, friendly_name: score} for (team, score) in team_scores.items()])
            return flask.Response(out.getvalue(), 200, mimetype='text/csv')
    
    @staticmethod
    def get_point_values(event_key: str, team: int, value_type: typing.Optional[str]):
        cur = db.connection().cursor()
        cur.row_factory = lambda cur, row: total_points(sqlite3.Row(cur, row), value_type) #type:ignore
        values = cur.execute(f"select * from frc2023{event_key}_match where teamNumber={team}").fetchall()
        netscore = sum(values)
        return special_divide(netscore, len(values))

    class BestDefense(flask_restful.Resource): #No way to make unweighted since kind of arbitrary
        def get(self, event: str):
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> float:
                netscore = 0
                total = 0
                for row in c.execute(f"select * from {table} where teamNumber={team}").fetchall():
                    resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/match/2023{event}_{row['match']}")
                    if not resp.ok:
                        return flask.abort(500, "[Analysis] Request Error. "+resp.text)
                    matchinfo = resp.json()
                    alliance = [a for a in matchinfo["alliances"] if f"frc{row['teamNumber']}" in matchinfo["alliances"][a]["team_keys"]]
                    if len(alliance) != 1:
                        print(f"[Analysis] Invalid Alliance. Team: {row['teamNumber']} @ Match: {row['match']}")
                        continue
                    alliance = alliance[0]
                    driverskill = row["commentsDriverrating"]/(5*(row["commentsFouls"]+1)*(0.7 if row["commentsDefensive"] == 1 else 1))
                    defensescore= matchinfo["score_breakdown"][alliance]["foulPoints"]-matchinfo["score_breakdown"][invert_alliance[alliance]]["teleopPoints"]
                    netscore += driverskill*defensescore
                    total += 1
                return special_divide(netscore, total)
            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            teams = dict(sorted(teams.items(), key=lambda item: item[1]))
            if flask.request.args.get("csv", "false") == "false":
                return teams
            else:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=["Team Number", "Defense Score"])
                writer.writeheader()
                writer.writerows([{"Team Number": team, "Defense Score": score} for (team, score) in teams.items()])
                return flask.Response(out.getvalue(), 200, mimetype='text/csv')

    class BestScoring(flask_restful.Resource):
        def get(self, event: str):
            return Analysis2023.ranking_wrapper(event, None)
    
    class BestAuto(flask_restful.Resource):
        def get(self, event: str):
            return Analysis2023.ranking_wrapper(event, 'auto')
    
    class BestTeleop(flask_restful.Resource):
        def get(self, event: str):
            return Analysis2023.ranking_wrapper(event, 'teleop')
    
    class BestEndgame(flask_restful.Resource):
        def get(self, event: str):
            return Analysis2023.ranking_wrapper(event, 'endgame')
    
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
                score_total += int(row["autoMobility"]) * SCORING_POINTS["autoMobility"] + int(row["autoDocked"]) * SCORING_POINTS["autoDocked"] + int(row["autoEngaged"]) * SCORING_POINTS["autoEngaged"]
            score_total += total_points(row, "auto") #idk if this might cause an error but my type checker marks it as red might want to take a look #type:ignore

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
    
    class SaturatedEvent(flask_restful.Resource):
        def get(self, event: str):
            tbamatches = get_with_cache(f"https://www.thebluealliance.com/api/v3/event/2023{event}/matches").json()
            tbamatches = {match['key'].split("_")[-1]: match for match in tbamatches}
            
            matches = []
            for dbdata in db.connection().cursor().execute(f"select * from frc2023{event}_match").fetchall():
                match = dbdata["match"]
                dbdata = dict(dbdata)
                tbadata = tbamatches[match]
                alliancelist = [a for a in tbadata["alliances"] if f"frc{dbdata['teamNumber']}" in tbadata["alliances"][a]["team_keys"]]
                if len(alliancelist) != 1:
                    print(f"[Analysis] Invalid Alliance. Team: {dbdata['teamNumber']} @ Match: {dbdata['match']}")
                    continue
                alliance: str = alliancelist[0]
                robotnumber: int = tbadata["alliances"][alliance]["team_keys"].index("frc"+str(dbdata['teamNumber']))+1
                if robotnumber > 3:
                    print(f"[Analysis] Invalid Robot Index Number. Team: {dbdata['teamNumber']} @ Match: {dbdata['match']}")
                    continue
                alliancescores = tbadata["score_breakdown"][alliance]
                autodocked = alliancescores["autoChargeStationRobot"+str(robotnumber)] == "Docked"
                endgamedocked = alliancescores["endGameChargeStationRobot"+str(robotnumber)] == "Docked"
                del dbdata["name"]
                del dbdata["commentsDriverComments"]
                del dbdata["commentsRobotComments"]
                matches.append({
                    **dbdata,
                    "activationBonusAchieved": alliancescores["activationBonusAchieved"],
                    "coopertitionCriteriaMet": alliancescores["coopertitionCriteriaMet"],
                    "sustainabilityBonusAchieved": alliancescores["sustainabilityBonusAchieved"],
                    "won": tbadata["winning_alliance"] == alliance,
                    "rp": alliancescores["rp"],

                    "autoMobility": alliancescores["mobilityRobot"+str(robotnumber)] == "Yes",
                    "autoDocked": autodocked,
                    "autoEngaged": autodocked and alliancescores["autoBridgeState"] == "Level",
                    "endgameParked": alliancescores["endGameChargeStationRobot"+str(robotnumber)] == "Park",
                    "endgameDocked": endgamedocked,
                    "endgameEngaged": endgamedocked and alliancescores["endGameBridgeState"] == "Level",
                    "commentsFouls":  max(dbdata["commentsFouls"] if "commentsFouls" in dbdata else 0, alliancescores["foulCount"]+alliancescores["techFoulCount"]),
                    "commentsDisqualified": "frc"+str(dbdata['teamNumber']) in tbadata["alliances"][alliance]["dq_team_keys"]
                })
            return matches

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
    "commentsFouls" :-5
}

def total_points(row: sqlite3.Row, startswith: typing.Optional[str] = None): #None is there for clarity's sake, empty string is more vague
    return sum([SCORING_POINTS[k]*v for k, v in dict(row).items() if k in SCORING_POINTS and (not startswith or k.startswith(startswith))])