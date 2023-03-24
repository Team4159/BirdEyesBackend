from pathlib import Path
import pathlib
import os
import json

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
        app.api: api.Api = a #type:ignore
        app.bluealliance: bluealliance.BlueAlliance = ba #type:ignore
        app.gr = g
    
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

    @app.route('/admin')
    def admin():
        return flask.send_file('static/admin.html')
    
    @app.get('/<int:season>/events/<string:event_id>/current_matches')
    def current_matches(season, event_id):
        tba_matches = bluealliance.BlueAlliance.BAEvent().get(season, event_id)
        sorted_matches = sorted(tba_matches.values(), key=lambda x: x['match_number'])
        sorted_unfinished_matches = filter(lambda x: x['actual_time'] == None, sorted_matches)
        
        # TODO: Also include which teams are assigned
        return flask.Response(json.dumps(sorted_unfinished_matches[0:2], sort_keys=False), 200, content_type='application/json')
    
    @app.post('/<int:season>/events/<string:event_id>/matches/<string:match_id>/scout')
    def start_scouting(season, event_id, match_id):
        master_file_path = f"teams/{season}-{event_id}-{match_id}-master.txt"
        unassiged_file_path = f"teams/{season}-{event_id}-{match_id}-unassigned.txt"
        
        if not os.path.isdir('teams'):
            os.makedirs('teams')
        
        if not os.path.exists(master_file_path):
            open(master_file_path, 'w')
            open(unassiged_file_path, 'w')

        else:
            with open(master_file_path, 'r') as master, open(unassiged_file_path, 'r+') as unassigned:
                lines = unassigned.readlines()
                if len(lines) == 0:
                    raise flask.Response('All teams assigned.', 404)
                else:
                    last = lines[-1]
                    unassigned.writelines(lines[:-1])
                    return flask.Response(json.dumps({"team_number": last}, sort_keys=False), 200, content_type='application/json')
                
    @app.post('/<int:season>/events/<string:event_id>/matches/<string:match_id>/stop_scouting/<string:team_number>')
    def stop_scouting(season, event_id, match_id, team_number):
        master_file_path = "~/teams/{season}-{event_id}-{match_id}-master.txt"
        unassiged_file_path = "~/teams/{season}-{event_id}-{match_id}-unassigned.txt"
        if not os.path.exists(master_file_path):
            return flask.Response('Match doesn\t exist', 404)
        else:
            with open(master_file_path, 'r') as master, open(unassiged_file_path, 'r+') as unassigned:
                unassigned_teams = unassigned.readlines()
                master_lines = master.readlines()
                if team_number in master_lines:
                    new_unassigned = unassigned_teams + [team_number]
                    unassigned.writelines(new_unassigned)
                    return flask.Response("{team_number} freed", 200)
                else:
                    return flask.Response("{team_number} not added to unassigned list because it is not in the master list")                
    
    return app