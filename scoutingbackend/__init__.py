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
        tba_matches = bluealliance.BlueAlliance.BAEventMatches().get(season, event_id)
        sorted_matches = sorted(tba_matches, key=lambda x: x['match_number'])
        sorted_unfinished_matches = [x for x in sorted_matches if x['actual_time'] == None]

        response_payload = []
        for match in sorted_unfinished_matches[0:2]:
            match_key = match['key'].split('_')[1]
            master_file_path = f"teams/{season}-{event_id}-{match_key}-master.txt"
            unassiged_file_path = f"teams/{season}-{event_id}-{match_key}-unassigned.txt"

            assigned_teams = set()
        
            if os.path.exists(master_file_path):
                with open(master_file_path, 'r') as master, open(unassiged_file_path, 'r') as unassigned:
                    unassigned_teams = set([x.strip() for x in unassigned.readlines()])
                    all_teams = set([x.strip() for x in master.readlines()])
                    assigned_teams = all_teams.difference(unassigned_teams)

            match_payload = {
                'key': match_key,
                'teams': []
            }
            
            for team in match['alliances']['blue']['team_keys']:
                team_name = team.replace('frc', '')
                match_payload['teams'].append({
                    'number': int(team_name),
                    'isAssigned': team_name in assigned_teams,
                    'color': 'blue'
                })
           
            for team in match['alliances']['red']['team_keys']:
                team_name = team.replace('frc', '')
                match_payload['teams'].append({
                    'number': int(team_name),
                    'isAssigned': team_name in assigned_teams,
                    'color': 'red'
                })
            
            response_payload.append(match_payload)

        return flask.Response(json.dumps(response_payload, sort_keys=False), 200, content_type='application/json')
    
    @app.route('/<string:season>/events/<string:event_id>/matches/<string:match_id>/scout', methods = ['POST'])
    def start_scouting(season, event_id, match_id):
        print("scouting started!!!!")
        master_file_path = f"teams/{season}-{event_id}-{match_id}-master.txt"
        unassiged_file_path = f"teams/{season}-{event_id}-{match_id}-unassigned.txt"
        
        if not os.path.isdir('teams'):
            print('making dir')
            os.makedirs('teams')
        
        if not os.path.exists(master_file_path):
            print('filling files')
            tba_match = bluealliance.BlueAlliance.BAMatch().get(season, event_id, match_id)
            tba_match_participants = tba_match.keys()
            tba_match_participants_string = '\n'.join(tba_match_participants)
            print('got participants', tba_match_participants_string)
            
            with open(master_file_path, 'w') as master, open(unassiged_file_path, 'w') as unassigned:
                master.write(tba_match_participants_string)
                unassigned.write(tba_match_participants_string)
                print('finished writing to files')

        with open(unassiged_file_path, 'r') as unassigned:
            print('start reading')
            lines = unassigned.readlines()
            print(lines)
            if len(lines) == 0:
                print('no lines')
                return flask.Response('All teams assigned.', 404)
            
        with open(unassiged_file_path, 'w') as unassigned:
            last = lines[-1].strip()
            unassigned.writelines(lines[:-1])
            return flask.Response(json.dumps({"team_number": int(last)}, sort_keys=False), 200, content_type='application/json')

    # Clients should hold the originally assigned team number, and if they start scouting another 
    # team and later cancel, the original team number should be sent to this endpoint.            
    @app.post('/<int:season>/events/<string:event_id>/matches/<string:match_id>/stop_scouting/<int:team_number>')
    def stop_scouting(season, event_id, match_id, team_number):
        master_file_path = f"teams/{season}-{event_id}-{match_id}-master.txt"
        unassiged_file_path = f"teams/{season}-{event_id}-{match_id}-unassigned.txt"
        if not os.path.exists(master_file_path):
            return flask.Response('Match, season, or event doesn\t exist', 404)
        
        with open(master_file_path, 'r') as master, open(unassiged_file_path, 'r') as unassigned:
            unassigned_teams = [line.strip() for line in unassigned.readlines()]
            master_list = [line.strip() for line in master.readlines()]
        
        if str(team_number) in master_list and str(team_number) not in unassigned_teams:
            with open(unassiged_file_path, 'w') as unassigned:
                new_unassigned = unassigned_teams + [str(team_number)]
                unassigned.writelines([line + '\n' for line in new_unassigned])
                return flask.Response(f"{team_number} freed", 200)
        
        elif str(team_number) in unassigned_teams:
            return flask.Response(f"{team_number} not freed because it is already unassigned")    
        else:
            return flask.Response(f"{team_number} not freed because it is not playing in this match")                
                

    @app.route('/testroute/<int:season>', methods = ['POST'])
    def test_route(season):
        print(f"hit test {season}")
        return flask.Response("you did it", 200)
    
    print(app.url_map)
    return app