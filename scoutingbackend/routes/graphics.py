import io
import itertools
import os
import pathlib
import typing
import matplotlib.pyplot

import flask
import flask_restful

from scoutingbackend.database import db
from scoutingbackend.routes.analysis import total_points

matplotlib.pyplot.ioff()

class Graphics2023(object):
    cache: typing.Optional[pathlib.Path] = None
    def __init__(self, cache_directory: typing.Optional[typing.Union[str, os.PathLike]]) -> None:
        if cache_directory:
            Graphics2023.cache = pathlib.Path(cache_directory)
        self.bp = flask.Blueprint('graphics', __name__, url_prefix='/graphics')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.JojoWheel, '/<int:year>/<string:event>/<int:team>/wheel')
        self.rest.add_resource(self.StatGraph, '/<int:year>/<string:event>/<int:team>/pointgraph')

    def register(self, app: typing.Union[flask.Flask, flask.Blueprint]):
        app.register_blueprint(self.bp)

    class JojoWheel(flask_restful.Resource):
        def get(self, year: int, event: str, team: int):
            if Graphics2023.cache:
                file = pathlib.Path(Graphics2023.cache, f"{year}_{team}.png")
            else:
                file = None
            if file and file.exists():
                return flask.Response(file.read_bytes(), 200, mimetype="image/png")
            else:
                cur = db.connection().cursor()
                teaminfo = cur.execute(f"SELECT * FROM frc{year}{event}_match WHERE (teamNumber={team})").fetchall()
                keylist = [
                    [[f"{gametime}{piece}{position}" for gametime in ('auto', 'teleop')] for position in ('misses', 'low', 'mid', 'high')] for piece in ('Cone', 'Cube')
                ]
                keylist = list(itertools.chain(*itertools.chain(*keylist)))
                all_miss = sum(sum(e[k] for k in keylist if k.endswith('misses')) for e in teaminfo)
                all_ok = sum(sum(e[k] for k in keylist if (not k.endswith('misses'))) for e in teaminfo)
                print(all_miss, all_ok)
    
    class StatGraph(flask_restful.Resource):
        def get(self, year: int, event: str, team: int):
            raw_data = db.connection().cursor().execute(f"SELECT * FROM frc{year}{event}_match WHERE teamNumber={team}").fetchall()
            matchids = []
            autopts = []
            telepts = []
            endgpts = []
            for match in raw_data:
                matchids.append(match['match'])
                totalauto = total_points(match, 'auto')
                totalteleop = total_points(match, 'teleop')
                totalendgame = total_points(match, 'endgame')
                if totalauto is None: #unlikely but possible
                    totalauto = 0
                if totalteleop is None:
                    totalteleop = 0
                if totalendgame is None:
                    totalendgame = 0
                autopts.append(totalauto)
                telepts.append(totalteleop)
                endgpts.append(totalendgame)
            matplotlib.pyplot.cla()
            matplotlib.pyplot.title(f"Team {team} Points")
            matplotlib.pyplot.xlabel("Match")
            matplotlib.pyplot.ylabel("Points")
            matplotlib.pyplot.stackplot(matchids, autopts, telepts, endgpts, labels=["Auto", "Teleop", "Endgame"])
            matplotlib.pyplot.legend(loc="upper left")
            out = io.BytesIO()
            matplotlib.pyplot.savefig(out, format='png')
            out.seek(0)
            return flask.Response(out.read(), 200, content_type='image/png')