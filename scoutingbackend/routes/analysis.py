import csv
import io
import typing

import flask
import flask_restful

from scoutingbackend.cachingsession import get_with_cache
from scoutingbackend.database import db
from scoutingbackend.schemes import invert_alliance

def special_divide(n, d):
    return n/d if d else 0

class Analysis2023(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('an', __name__, url_prefix='/analysis/2023')
        self.rest = flask_restful.Api(self.bp)
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
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> dict[str, float]:
                netscore = 0
                rawscore = 0
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
                    rawscore += total_points(row)
                    netscore += special_divide(total_points(row), matchinfo["score_breakdown"][alliance]["totalPoints"])
                    total += 1
                return {"rawaverage": special_divide(rawscore, total), "weightedscore": special_divide(netscore, total)}

            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            teams = dict(sorted(teams.items(), key=lambda item: item[1]["weightedscore"], reverse=True))
            if flask.request.args.get("csv", "false") == "false":
                return teams
            else:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=["Team Number", "Offense Score", "Raw Average"])
                writer.writeheader()
                writer.writerows([{"Team Number": team, "Offense Score": score["weightedscore"], "Raw Average": score["rawaverage"]} for (team, score) in teams.items()])
                return flask.Response(out.getvalue(), 200, mimetype='text/csv')
    
    class BestAuto(flask_restful.Resource):
        def get(self, event: str):
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> dict[str, float]:
                netscore = 0
                rawscore = 0
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
                    rawscore += total_points(row, "auto")
                    netscore += special_divide(total_points(row, "auto"), matchinfo["score_breakdown"][alliance]["autoPoints"])
                    total += 1
                return {"rawaverage": special_divide(rawscore, total), "weightedscore": special_divide(netscore, total)}
            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            teams = dict(sorted(teams.items(), key=lambda item: item[1]["weightedscore"], reverse=True))
            if flask.request.args.get("csv", "false") == "false":
                return teams
            else:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=["Team Number", "Auto Score", "Raw Average"])
                writer.writeheader()
                writer.writerows([{"Team Number": team, "Auto Score": score["weightedscore"], "Raw Average": score["rawaverage"]} for (team, score) in teams.items()])
                return flask.Response(out.getvalue(), 200, mimetype='text/csv')
    
    class BestTeleop(flask_restful.Resource):
        def get(self, event: str):
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> dict[str, float]:
                netscore = 0
                rawscore = 0
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
                    rawscore += total_points(row, "teleop")
                    netscore += special_divide(total_points(row, "teleop"), matchinfo["score_breakdown"][alliance]["teleopPoints"])
                    total += 1
                return {"rawaverage": special_divide(rawscore, total), "weightedscore": special_divide(netscore, total)}
            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            teams = dict(sorted(teams.items(), key=lambda item: item[1]["weightedscore"], reverse=True))
            if flask.request.args.get("csv", "false") == "false":
                return teams
            else:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=["Team Number", "Teleop Score", "Raw Average"])
                writer.writeheader()
                writer.writerows([{"Team Number": team, "Teleop Score": score['weightedscore'], "Raw Average": score["rawaverage"]} for (team, score) in teams.items()])
                return flask.Response(out.getvalue(), 200, mimetype='text/csv')
    
    class BestEndgame(flask_restful.Resource):
        def get(self, event: str):
            c = db.connection().cursor()
            table = f"frc2023{event}_match"
            def k(team: str) -> dict[str, float]:
                netscore = 0
                rawscore = 0
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
                    rawscore += total_points(row, "endgame")
                    netscore += special_divide(total_points(row, "endgame"), (matchinfo["score_breakdown"][alliance]["endGameParkPoints"]+matchinfo["score_breakdown"][alliance]["endGameChargeStationPoints"]))
                    total += 1
                return {"rawaverage": special_divide(rawscore, total), "weightedscore": special_divide(netscore, total)}
            teams = {team: k(team) for team in set(t["teamNumber"] for t in c.execute(f"select (teamNumber) from " + table).fetchall())}
            teams = dict(sorted(teams.items(), key=lambda item: item[1]["weightedscore"], reverse=True))
            if flask.request.args.get("csv", "false") == "false":
                return teams
            else:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=["Team Number", "Endgame Score", "Raw Average"])
                writer.writeheader()
                writer.writerows([{"Team Number": team, "Endgame Score": score['weightedscore'], "Raw Average": score["rawaverage"]} for (team, score) in teams.items()])
                return flask.Response(out.getvalue(), 200, mimetype='text/csv')
    
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
            tbamatches = get_with_cache(f"https://www.thebluealliance.com/api/v3/event/2023{event}/matches")
            tbamatches = {match["event_key"]: match for match in tbamatches}
            dbmatches = db.connection().cursor().execute(f"select * from frc2023{event}_match").fetchall()
            dbmatches = {row["match"]: dict(row) for row in dbmatches}
            
            matches = dbmatches
            for match, tbadata in tbamatches:
                matches[match] = dbmatches[match] if match in dbmatches else {}
                

            return {} # TODO: Implement

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

def total_points(row, startswith = ""):
    return sum([SCORING_POINTS[k]*v for k, v in dict(row).items() if k in SCORING_POINTS and k.startswith(startswith)])