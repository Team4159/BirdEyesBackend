from pathlib import Path
import pathlib

import flask
import flask_cors

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
        #app.context_processor
        a = api.Api()
        ba = bluealliance.BlueAlliance(app.config["TBA_KEY"])
        ba.register(a.bp) # /api/bluealliance
        an = analysis.Analysis2023()
        an.register(a.bp) # /api/analysis
        g = graphics.Graphics2023(app.config['MANUAL_CACHE'])
        g.register(a.bp) # /api/graphics
        a.register(app) # /api/

        # if you want to access bluealliance functions (WARNING: may work slightly funny), you can now use current_app.api/current_app.bluealliance.xyz
        app.api: api.Api = a
        app.bluealliance: bluealliance.BlueAlliance = ba
    
    pathlib.Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    
    @app.route('/')
    def test(): return "BirdsEye Scouting Server Online!"
    
    return app