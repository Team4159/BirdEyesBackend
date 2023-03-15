import itertools
import os
import pathlib
import typing

import flask
import flask_restful

from scoutingbackend.database import db


class Graphics2023(object):
    cache: typing.Optional[pathlib.Path] = None
    def __init__(self, cache_directory: typing.Optional[typing.Union[str, os.PathLike]]) -> None:
        if cache_directory:
            Graphics2023.cache = pathlib.Path(cache_directory)
        self.bp = flask.Blueprint('graphics', __name__, url_prefix='/graphics')
        self.rest = flask_restful.Api(self.bp)
        self.rest.add_resource(self.JojoWheel, '/<int:year>/<string:event>/<int:team>/wheel')

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