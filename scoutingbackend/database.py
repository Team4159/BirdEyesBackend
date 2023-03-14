import os
import sqlite3
import typing

from scoutingbackend import schemes


class Database(object):
    def connect(self, location: typing.Union[os.PathLike, str]) -> None:
        self.loc = location
        
    def connection(self):
        if not hasattr(self, 'loc'):
            raise RuntimeError("Database has not connected yet")
        c = sqlite3.connect(self.loc)
        c.row_factory = sqlite3.Row
        return c
    
    def create_tables(self, season: int, event: str):
        table_name = f"frc{season}{event}"
        eschema_middle = ", ".join(f"{name} {type_}" for name, type_ in flatten(schemes.MATCH_SCHEME[str(season)]).items())
        pschema_middle = ", ".join(f"{question_name} TEXT" for question_name in schemes.PIT_SCHEME[str(season)].values())
        eschema = f"CREATE TABLE IF NOT EXISTS {table_name}_match (match TEXT NOT NULL, teamNumber INTEGER NOT NULL, name TEXT NOT NULL, {eschema_middle}, PRIMARY KEY (match, teamNumber));"
        pschema = f"CREATE TABLE IF NOT EXISTS {table_name}_pit (teamNumber INTEGER NOT NULL, name TEXT NOT NULL, {pschema_middle}, PRIMARY KEY (teamNumber, name));"

        c = self.connection()
        c.cursor().executescript(eschema).executescript(pschema)
        c.commit()

db = Database() #idk if this is okay it probably isn't should probably be context-specific

def flatten(scheme: dict[str, dict[str, str]]) -> dict[str, str]:
    out = {}
    for k, v in scheme.items():
        for k1, v1 in v.items():
            out[k+k1.capitalize()] = schemes.MATCH_SCHEME_DATATYPES[v1]
    return out

def generate_selector(argdict: dict):
    return ("WHERE "+" AND ".join([f"{k}=\"{v}\"" for k,v in argdict.items() if not v == None])) if len(argdict) > 0 else ""