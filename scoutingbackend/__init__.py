import json
import os

from flask import Flask
from flask_cors import CORS

from . import api

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'scouting.sqlite'),
    )
    CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    app.register_blueprint(api.bp)
    return app
