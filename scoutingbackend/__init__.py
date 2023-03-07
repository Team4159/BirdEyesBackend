from pathlib import Path

import flask
import flask_cors

from scoutingbackend.database import db
from scoutingbackend.routes import api, bluealliance, analysis


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
        
        a = api.Api()
        ba = bluealliance.BlueAlliance(app.config["TBA_KEY"])
        ba.register(a.bp)
        an = analysis.Analysis2023()
        an.register(a.bp)
        a.register(app)
        
    @app.route('/')
    def test(): return "BirdsEye Scouting Server Online!"
    
    return app