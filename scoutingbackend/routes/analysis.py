import typing

import flask
import flask_restful

from scoutingbackend.cachingsession import get_with_cache
from scoutingbackend.database import db
from scoutingbackend.schemes import invert_alliance


class Analysis(object):
    def __init__(self) -> None:
        self.bp = flask.Blueprint('an', __name__, url_prefix='/analysis')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.BestDefense, '/<int:season>/<string:event>/bestDefense')
        self.rest.add_resource(self.BestOffense, '/<int:season>/<string:event>/bestOffense')
        self.rest.add_resource(self.BestAuto, '/<int:season>/<string:event>/bestAuto')
        # self.rest.add_resource(self.ApiPSchema, '/<int:season>/<string:event>/pickup')
    
    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)

    class BestDefense(flask_restful.Resource):
        def get(self, season: int, event: str):
            c = db.connection().cursor()
            if season == 2023:
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
            else:
                return flask.abort(404, description="No analysis available for "+season)
    
    class BestOffense(flask_restful.Resource):
        def get(self, season: int, event: str):
            # c = db.connection().cursor()
            if season == 2023:
            #     table = f"frc2023{event}_match"
            #     def k(team: str) -> float:
            #         netscore = 0
            #         total = 0
            #         for row in c.execute(f"select * from {table} where teamNumber={team}").fetchall():
            #             resp = get_with_cache(f"https://www.thebluealliance.com/api/v3/match/2023{event}_{row['match']}")
            #             if not resp.ok:
            #                 raise Exception(f"[Analysis] Request Error. "+resp.text)
            #             matchinfo = resp.json()
            #             alliance = [a for a in matchinfo["alliances"] if f"frc{row['teamNumber']}" in matchinfo["alliances"][a]["team_keys"]]
            #             if len(alliance) != 1:
            #                 raise Exception(f"[Analysis] Invalid Alliance. Team: {row['teamNumber']} @ Match: {row['match']}")
            #             alliance = alliance[0]
            #             driverskill = row["commentsDriverrating"]/(5*(row["commentsFouls"]+1)*(0.7 if row["commentsDefensive"] == 1 else 1))
            #             3*total_score(row)/matchinfo["teleopPoints"]
            #             netscore += driverskill*defensescore
            #             total += 1
            #         return netscore/total
                return {}
            else:
                return flask.abort(404, description="No analysis available for "+season)
    
    class BestAuto(flask_restful.Resource):
        def get(self, season: int, event: str):
            if season == 2023:
                return {}
            else:
                return flask.abort(404, description="No analysis available for "+season)