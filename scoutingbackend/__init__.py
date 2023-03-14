from pathlib import Path

import flask
import flask_cors
import typing

from scoutingbackend.database import db
from scoutingbackend.routes import api, bluealliance, analysis, graphics

def create_app():
    app = flask.Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=str(Path(app.instance_path, 'scoutingdb.sqlite')),
        MANUAL_CACHE=str(Path(app.instance_path, 'manual_cache'))
    )
    app.config.from_pyfile(str(Path(app.instance_path, 'config.py')))
    flask_cors.CORS(app, origins="*")
    db.connect(app.config['DATABASE'])
    
    with app.app_context():
        bluealliance.session.set_manual_cache(app.config['MANUAL_CACHE'])
        app.context_processor
        a = api.Api()
        ba = bluealliance.BlueAlliance(app.config["TBA_KEY"])
        ba.register(a.bp)
        an = analysis.Analysis2023()
        an.register(a.bp)
        a.register(app)
        g = graphics.Graphics2023(app.config['MANUAL_CACHE'])
        g.register(app)
        
        # type checkers complain here but that's what python is about
        # if you want to access bluealliance functions (WARNING: may work slightly funny), you can now use current_app.api/current_app.bluealliance.xyz
        app.api: api.Api = a #type:ignore
        app.bluealliance: bluealliance.BlueAlliance = ba #type:ignore
    
    pathlib.Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    
    @app.route('/')
    def test(): return "BirdsEye Scouting Server Online!"
    
    #example for calling routes as functions from other routes
    @app.route('/TEST')
    def testt():
        #override the request ignoreDate with this one
        #if unset, season.get would use whatever is in `url/TEST?ignoreDate=foo` or the function's default
        flask.g.args = {'ignoreDate': 'true'}
        o = {'a': flask.current_app.bluealliance.season.get(2023)} #type:ignore
        flask.g.args = {'teamNumber': 4158}
        o['b'] = flask.current_app.api.pit.get(2023, 'casf') #type:ignore
        flask.g.args = {'teamNumber': 4159}
        o['c'] = flask.current_app.api.pit.get(2023, 'casf') #type:ignore
        return o
    
    return app