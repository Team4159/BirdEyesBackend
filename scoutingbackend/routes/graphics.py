import io
import itertools
import os
import pathlib
import typing
from matplotlib import pyplot

import flask
import flask_restful

from scoutingbackend.database import db
from scoutingbackend.routes.analysis import total_points

pyplot.ioff()

class Graphics2023(object):
    cache: typing.Optional[pathlib.Path] = None
    def __init__(self, cache_directory: typing.Optional[typing.Union[str, os.PathLike]]) -> None:
        if cache_directory:
            Graphics2023.cache = pathlib.Path(cache_directory)
        self.bp = flask.Blueprint('graphics', __name__, url_prefix='/graphics/2023')

        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.JojoWheel, '/<string:event>/<int:team>/wheel')
        self.rest.add_resource(self.StatGraph, '/<string:event>/<int:team>/statGraph')

    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)

    class JojoWheel(flask_restful.Resource):
        def get(self, event: str, team: int):
            if Graphics2023.cache:
                file = pathlib.Path(Graphics2023.cache, f"2023_{team}.png")
            else:
                file = None
            if file and file.exists():
                return flask.Response(file.read_bytes(), 200, mimetype="image/png")
            else:
                cur = db.connection().cursor()
                teaminfo = cur.execute(f"SELECT * FROM frc2023{event}_match WHERE (teamNumber={team})").fetchall()
                keylist = [
                    [[f"{gametime}{piece}{position}" for gametime in ('auto', 'teleop')] for position in ('misses', 'low', 'mid', 'high')] for piece in ('Cone', 'Cube')
                ]
                keylist = list(itertools.chain(*itertools.chain(*keylist)))
                all_miss = sum(sum(e[k] for k in keylist if k.endswith('misses')) for e in teaminfo)
                all_ok = sum(sum(e[k] for k in keylist if (not k.endswith('misses'))) for e in teaminfo)
                print(all_miss, all_ok)
    
    class StatGraph(flask_restful.Resource):
        def get(self, event: str, team: int):
            matches = db.connection().cursor().execute(f"SELECT * FROM frc2023{event}_match WHERE (teamNumber={team})").fetchall()
            if len(matches) == 0:
                return flask_restful.abort(404, description="No Matches Found!")
            matchids = []
            autopts = []
            telepts = []
            endgpts = []
            for match in matches:
                matchids.append(match['match'])
                totalauto = total_points(match, 'auto')
                totalteleop = total_points(match, 'teleop')
                totalendgame = total_points(match, 'endgame')
                autopts.append(totalauto)
                telepts.append(totalteleop)
                endgpts.append(totalendgame)
            pyplot.cla()
            pyplot.title(f"Team {team} Points")
            pyplot.xlabel("Match")
            pyplot.ylabel("Points")
            pyplot.stackplot(matchids, autopts, telepts, endgpts, labels=["Auto", "Teleop", "Endgame"])
            pyplot.legend(loc="upper left")
            pyplot.autoscale()
            out = io.BytesIO()
            pyplot.savefig(out, format='png')
            return flask.Response(out.getvalue(), 200, content_type='image/png')