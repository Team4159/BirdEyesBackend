import sqlite3

import click
from flask import current_app, g
import json
import base64
import typing
from scoutingbackend.schemes import *
    
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db():
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

class SimpleConnection(object):
    def __init__(self, table: str, cursor: sqlite3.Cursor) -> None:
        self.table = table
        self.cursor = cursor
        self.cursor.row_factory = sqlite3.Row # type: ignore
                
    def load_schema(self, schema: str):
        self.cursor.executescript(schema)
        self.cursor.connection.commit()
        
    def load_generic_schema(self, keyName: str, dataName: str):
        self.cursor.executescript(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                {keyName} STRING PRIMARY KEY NOT NULL,
                {dataName} STRING NOT NULL
            );""")
        self.cursor.connection.commit()
        
            
    def insert(self, data: list[typing.Any] | dict[str, typing.Any]) -> None:
        if isinstance(data, list):
            self.cursor.execute(f"INSERT INTO {self.table} VALUES ({', '.join('?' for _ in data)})", *data)
        elif isinstance(data, dict):
            ks = data.keys()
            self.cursor.execute(f"INSERT INTO {self.table} ({', '.join(k for k in ks)}) VALUES ({', '.join(f':{k}' for k in ks)})", data)
        self.cursor.connection.commit()
    
    def cache(self, kn, kv, ok, ov):
        cache_ready = json.dumps(ov)
        self.insert(**{kn:kv, ok:cache_ready})
    
    def uncache(self, kn, kv, ok):
        return json.dumps(self.fetch_one(**{kn:kv})[ok])
    
    def contains(self, **kwargs) -> bool:
        return bool(self.fetch_one(**kwargs))
        
    def fetch(self, **kwargs) -> sqlite3.Cursor:
        return self.cursor.execute(f"SELECT * FROM {self.table} WHERE {' AND '.join(f'{key} = :{key}' for key in kwargs.keys())}", kwargs)
    
    def fetch_multiple(self, **kwargs) -> list[sqlite3.Row]:
        return self.fetch(**kwargs).fetchall()
    
    def fetch_one(self, **kwargs) -> sqlite3.Row:
        return self.fetch(**kwargs).fetchone()

class CacheConnector(object):
    def __init__(self):
        self.db = sqlite3.connect(self.conf.general.cache_file)
    
    def get_cursor(self):
        return self.db.cursor()
    
    def create_simple(self, table: str) -> SimpleConnection:
        return SimpleConnection(table, self.get_cursor())

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def generate_selector(argdict: dict):
    return ("WHERE "+" AND ".join([f"{k}={v}" for k,v in argdict.items() if not v == None])) if len(argdict) > 0 else ""