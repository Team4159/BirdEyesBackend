import os

from flask import Flask
from flask_cors import CORS

from . import api

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'scouting.sqlite'),
    )

    # Initialize Cross-Origin support
    CORS(app)

    # initialize databases
    #TODO: rewrite into classes so this isn't such a pain
    from . import db
    db.init_app(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    @app.route('/') # To validate server ip
    def test():
        return 'BirdsEye Scouting Server Online!'
    
    app.register_blueprint(api.bp)
    return app
