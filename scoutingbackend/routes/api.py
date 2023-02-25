import json
import sqlite3

from flask import Blueprint, Response, abort, request, current_app, Flask
from . import bluealliance

from .. import schemes
from .. import db


class ApiRoutes(object):
    bp = Blueprint('api', __name__, url_prefix='/api')
    def __init__(self, api_key: str | None) -> None:
        self.ba_key = api_key
        self.ba = bluealliance.BlueAllianceRoutes(self.ba_key)
    
    def register(self, app: Flask | Blueprint):
        self.ba.register(self.bp)
        app.register_blueprint(self.bp)

    @bp.route('/<season>/listEvents', methods=("GET",))
    def route_list_events(season):
        tablenames = current_app.db.get_cursor().execute("SELECT name from sqlite_master WHERE type='table'").fetchall() #type:ignore
        tablenames = [e['name'] for e in tablenames if e['name'].startswith(f'frc{season}')]
        return json.dumps(tablenames)
    
    @bp.route('/<season>/createEvent', methods=('PUT',))
    def route_create_event(season):
        if season not in schemes.MATCH_SCHEME or season not in schemes.PIT_SCHEME or not request.data:
            return abort(Response("Unrecognized Season / Bad Data", 400))
        current_app.db.get_cursor().create_event(request.data.decode('utf8'), season) #type:ignore
        return Response("", 200)
    
    @bp.route('/<season>/matchschema/', methods=("GET",))
    def route_matchschema(season):
        if season not in schemes.MATCH_SCHEME:
            return abort(404)
        return Response(json.dumps(schemes.MATCH_SCHEME[season], sort_keys=False), 200, content_type='application/json')
    
    @bp.route('/<season>/pitschema')
    def route_pitschema(season):
        if season not in schemes.PIT_SCHEME:
            return abort(404)
        return schemes.PIT_SCHEME[season]
    
    @bp.route('/<season>/<event>/pit/', methods=('POST', 'GET'))
    def route_pit_wrapper(season, event):
        event = f"frc{season}{event}"
        if request.method == 'POST':
            return ApiRoutes.route_pit_post(season, event)
        elif request.method == 'GET':
            return ApiRoutes.route_pit_get(season, event)
        else:
            return abort(405)

    @staticmethod
    def route_pit_post(season, event):
        event_id = f"frc{season}{event}"
        data = request.get_json(True)
        try:
            current_app.db.get_cursor().execute(f"INSERT INTO {event_id}_pit ( {', '.join(schemes.PIT_SCHEME[season].values())+', teamNumber'} ) VALUES ( {', '.join(['?'] * len(data))} )", list(data.values()))
        except sqlite3.OperationalError as e:
            return abort(Response(type(e).__name__+" "+str(e), 500))
        current_app.db.get_db().commit()
        return Response(f"Successfully Added Pit Response! (#{data['teamNumber']})", 200)

    @staticmethod
    def route_pit_get(season, event):
        try:
            vals = current_app.db.get_cursor().execute(f"SELECT * FROM {event}_pit " + db.generate_selector(request.args))
        except sqlite3.OperationalError as e:
            return abort(Response(type(e).__name__+" "+str(e), 404))
        if not vals:
            return abort(404)
        return [dict(v) for v in vals]
    
    @bp.route('/<season>/<event>/match/', methods=('POST', 'GET'))
    def route_match_wrapper(season, event):
        event = f"frc{season}{event}"
        if request.method == 'POST':
            return ApiRoutes.route_match_post(event)
        elif request.method == 'GET':
            return ApiRoutes.route_match_get(event)
        else:
            return abort(405)
    
    @staticmethod
    def route_match_post(event: str):
        j = request.get_json(force=True)
        try:
            jp = {}
            for k, v in j["form"].items():
                for k1, v1 in v.items():
                    jp[k+k1[0].upper()+k1[1:]] = v1
            jp["teamNumber"] = j["teamNumber"]
            jp["match"] = j["match"]
            jp['name'] = j['name']
            
            current_app.db.get_cursor().execute(f"INSERT INTO {event}_match ( {', '.join(jp.keys())} ) VALUES ( {', '.join(['?'] * len(jp))} )", list(jp.values()))
        except sqlite3.OperationalError as e:
            return abort(Response(str(e), 404))
        current_app.db.get_cursor().commit()
        return Response(f"Successfully Added Match Response! (#{jp['teamNumber']} @ {jp['match']})", 200)

    @staticmethod
    def route_match_get(event):
        try:
            vals = current_app.db.get_cursor().execute(f"SELECT * FROM {event}_match "+db.generate_selector(request.args))
        except sqlite3.OperationalError as e:
            return abort(Response(str(e), 404))
        if not vals:
            return abort(404)
        return [dict(v) for v in vals]


#bp = Blueprint('api', __name__, url_prefix='/api')
#bp.register_blueprint(bluealliance.bp)

# @bp.route('/<season>/listEvents', methods=('GET',))
# def get_season_events(season):
#     tablenames = db.get_db().execute("SELECT name from sqlite_master WHERE type='table'").fetchall()
#     tablenames = [e['name'] for e in tablenames if e['name'].startswith(f'frc{season}')]
#     return json.dumps(tablenames)

# @bp.route('/<season>/createEvent', methods=("PUT",))
# def create_event(season):
#     if season not in MATCH_SCHEME or season not in PIT_SCHEME or request.data == None:
#         return abort(Response("Unrecognized Season / Bad Data", 400))
#     c = db.get_db()
#     c.executescript(db.DB_SCHEME[season].format(event=format_event(season, request.data.decode())))
#     c.commit()
#     return Response("Table Created / Already Exists", 200)

# @bp.route('/<season>/matchschema/', methods=("GET",))
# def eventmatchschema(season):
#     return Response(json.dumps(MATCH_SCHEME[season], sort_keys=False), 200, content_type='application/json') if season in MATCH_SCHEME else abort(404)

# @bp.route('/<season>/pitschema/', methods=("GET",))
# def pit_schema(season):
#     return PIT_SCHEME[season] if season in PIT_SCHEME else abort(404)

# @bp.route('/<season>/<event>/pit/', methods=('POST', 'GET',)) #type:ignore
# def pit(season, event):
#     eventCode = format_event(season, event)
#     c = db.get_db()
#     if request.method == "POST":
#         j = request.get_json(force=True)
#         try:
#             c.execute(f"INSERT INTO {eventCode}_pit ( {', '.join(PIT_SCHEME[season].values())+', teamNumber'} ) VALUES ( {', '.join(['?'] * len(j))} )", list(j.values()))
#         except sqlite3.OperationalError as e:
#             return abort(Response(type(e).__name__+" "+str(e), 500))
#         c.commit()
#         return Response(f"Successfully Added Pit Response! (#{j['teamNumber']})", 200)
#     elif request.method == "GET":
#         try:
#             vals = c.execute(f"SELECT * FROM {eventCode}_pit " + db.generate_selector(request.args))
#         except sqlite3.OperationalError as e:
#             return abort(Response(type(e).__name__+" "+str(e), 404))
#         if not vals:
#             return abort(404)
#         return [dict(v) for v in vals]

# @bp.route('/<season>/<event>/match/', methods=('POST', 'GET',)) #type:ignore
# def match(season, event):
#     eventCode = format_event(season, event)
#     c = db.get_db()
#     if request.method == "POST":
#         j = request.get_json(force=True)
#         try:
#             jp = {}
#             for k, v in j["form"].items():
#                 for k1, v1 in v.items():
#                     jp[k+k1[0].upper()+k1[1:]] = v1
#             jp["teamNumber"] = j["teamNumber"]
#             jp["match"] = j["match"]
#             jp['name'] = j['name']
            
#             c.execute(f"INSERT INTO {eventCode}_match ( {', '.join(jp.keys())} ) VALUES ( {', '.join(['?'] * len(jp))} )", list(jp.values()))
#         except sqlite3.OperationalError as e:
#             return abort(Response(str(e), 404))
#         c.commit()
#         return Response(f"Successfully Added Match Response! (#{jp['teamNumber']} @ {jp['match']})", 200)
#     elif request.method == "GET":
#         try:
#             vals = c.execute(f"SELECT * FROM {eventCode}_match "+db.generate_selector(request.args))
#         except sqlite3.OperationalError as e:
#             return abort(Response(str(e), 404))
#         if not vals:
#             return abort(404)
#         return [dict(v) for v in vals]