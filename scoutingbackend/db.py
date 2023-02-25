import sqlite3

import click
from flask import current_app, g
import json
import base64
import typing
import typing
from . import schemes

def generate_selector(argdict: dict):
    return ("WHERE "+" AND ".join([f"{k}={v}" for k,v in argdict.items() if not v == None])) if len(argdict) > 0 else ""
    
class EasyCaching(object):
    def __init__(self, connection: sqlite3.Connection, tablename: str, schema: dict={"key": "key", "value": "data"}, b64ify=False) -> None:
        self.conn = connection
        self.cursor = self.conn.cursor()
        self.tablename = tablename
        self.schema = schema
        self.b64ify = b64ify

        self.cursor.executescript(f"""
        CREATE TABLE IF NOT EXISTS {self.tablename} (
            {self.schema['key']} TEXT PRIMARY KEY NOT NULL,
            {self.schema['value']} TEXT PRIMARY KEY NOT NULL
        );
        """)
        self.conn.commit()
    
    def cache(self, key: str, value: typing.Any):
        jdat = json.dumps(value)
        if self.b64ify:
            jdat = base64.b64encode(jdat.encode('utf8')).decode('utf8')
        self.cursor.execute(f"INSERT INTO {self.tablename} ({self.schema['key']}, {self.schema['value']}) VALUES (?, ?)", (key, jdat))
        self.conn.commit()
    
    def uncache(self, key: str) -> typing.Any:
        res = self.cursor.execute(f"SELECT * FROM {self.tablename} WHERE {self.schema['key']}=?", (key,)).fetchone()[self.schema['value']]
        if self.b64ify:
            raw = base64.b64decode(res)
        else:
            raw = res
        return json.dumps(raw)
        
class Database(object):
    def __init__(self, app) -> None:
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        app.teardown_appcontext(self.close_db)

    def get_db(self) -> sqlite3.Connection: #in-context
        if 'db' not in g:
            d = sqlite3.connect(current_app.config['DATABASE'])
            d.row_factory = sqlite3.Row
            g.db = d
        return g.db
    
    def get_cursor(self) -> sqlite3.Cursor:
        return self.get_db().cursor()
    
    def close_db(self, *args, **kwargs) -> None: #in-context
        db = g.pop('db', None)
        if db is not None:
            db.close()
    
    def get_cache(self, tablename: str, schema: dict | None = None, b64ify: bool = False) -> EasyCaching: #in-context
        if not schema:
            return EasyCaching(self.get_db(), tablename, b64ify=b64ify)
        else:
            return EasyCaching(self.get_db(), tablename, schema, b64ify=b64ify)
    
    #utility functions
    def create_event(self, event_id: str, year: str):
        table_name = f"frc{year}{event_id}"
        flattened_scheme = schemes.flatten(schemes.MATCH_SCHEME[year])
        eschema_middle = ", ".join(f"{name} {type_}" for name, type_ in flattened_scheme)
        pschema_middle = ", ".join(f"{question_name} TEXT" for question_name in schemes.PIT_SCHEME[year].values())
        eschema = f"""CREATE TABLE IF NOT EXISTS {table_name}_match (match TEXT NOT NULL, teamNumber INTEGER NOT NULL, scouter TEXT NOT NULL, {eschema_middle}, PRIMARY KEY (match, teamNumber));"""
        pschema = f"""CREATE TABLE IF NOT EXISTS {table_name}_pit (teamNumber INTEGER PRIMARY KEY NOT NULL, name TEXT NOT NULL, {pschema_middle});"""

        db=self.get_db()
        db.cursor().executescript(eschema)
        db.cursor().executescript(pschema)
        db.commit()
    
# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(
#             current_app.config['DATABASE'],
#             detect_types=sqlite3.PARSE_DECLTYPES
#         )
#         g.db.row_factory = sqlite3.Row

#     return g.db

# def close_db(e=None): #e=None is IMPORTANT
#     db = g.pop('db', None)

#     if db is not None:
#         db.close()

# class SimpleConnection(object):
#     def __init__(self, table: str, cursor: sqlite3.Cursor) -> None:
#         self.table = table
#         self.cursor = cursor
#         self.cursor.row_factory = sqlite3.Row # type: ignore
                
#     def load_schema(self, schema: str):
#         self.cursor.executescript(schema)
#         self.cursor.connection.commit()
        
#     def load_generic_schema(self, keyName: str, dataName: str):
#         self.cursor.executescript(f"""
#             CREATE TABLE IF NOT EXISTS {self.table} (
#                 {keyName} STRING PRIMARY KEY NOT NULL,
#                 {dataName} STRING NOT NULL
#             );""")
#         self.cursor.connection.commit()
        
            
#     def insert(self, data: list[typing.Any] | dict[str, typing.Any]) -> None:
#         if isinstance(data, list):
#             self.cursor.execute(f"INSERT INTO {self.table} VALUES ({', '.join('?' for _ in data)})", *data)
#         elif isinstance(data, dict):
#             ks = data.keys()
#             self.cursor.execute(f"INSERT INTO {self.table} ({', '.join(k for k in ks)}) VALUES ({', '.join(f':{k}' for k in ks)})", data)
#         self.cursor.connection.commit()
    
#     def cache(self, kn, kv, ok, ov):
#         cache_ready = json.dumps(ov)
#         self.insert({kn:kv, ok:cache_ready})
    
#     def uncache(self, kn, kv, ok):
#         return json.loads(self.fetch_one(**{kn:kv})[ok])
    
#     def contains(self, **kwargs) -> bool:
#         return bool(self.fetch_one(**kwargs))
        
#     def fetch(self, **kwargs) -> sqlite3.Cursor:
#         return self.cursor.execute(f"SELECT * FROM {self.table} WHERE {' AND '.join(f'{key} = :{key}' for key in kwargs.keys())}", kwargs)
    
#     def fetch_multiple(self, **kwargs) -> list[sqlite3.Row]:
#         return self.fetch(**kwargs).fetchall()
    
#     def fetch_one(self, **kwargs) -> sqlite3.Row:
#         return self.fetch(**kwargs).fetchone()

# class CacheConnector(object):
#     def __init__(self, db: sqlite3.Connection):
#         self.db = db
    
#     def get_cursor(self):
#         return self.db.cursor()
    
#     def create_simple(self, table: str) -> SimpleConnection:
#         return SimpleConnection(table, self.get_cursor())


# def init_db():
#     db = get_db()

#     sqlite3.register_adapter(bool, int)
#     sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

#     CacheConnector(db).create_simple("blueallianceCache").load_generic_schema("route", "data")

# @click.command('init-db')
# def init_db_command():
#     """Clear the existing data and create new tables."""
#     init_db()
#     click.echo('Initialized the database.')

# def init_app(app):
#     app.teardown_appcontext(close_db)
#     app.cli.add_command(init_db_command)

# def generate_selector(argdict: dict):
#     return ("WHERE "+" AND ".join([f"{k}={v}" for k,v in argdict.items() if not v == None])) if len(argdict) > 0 else ""

# def get_connector():
#     return CacheConnector(get_db())