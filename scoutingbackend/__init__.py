import os

from flask import Flask, current_app
from flask_cors import CORS

from .routes import api
from . import db

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'scouting.sqlite'),
    )

    with app.app_context():
        current_app.db = db.Database(app) #type:ignore


    # Initialize Cross-Origin support
    CORS(app)

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
