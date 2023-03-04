import os
import sqlite3
import typing


class Database(object):
    def connect(self, location: typing.Union[os.PathLike, str]) -> None:
        self.loc = location
        
    def connection(self):
        if not hasattr(self, 'loc'):
            raise RuntimeError("Database has not connected yet")
        c = sqlite3.connect(self.loc)
        c.row_factory = sqlite3.Row
        return c
    
    def cursor(self):
        if not hasattr(self, 'loc'):
            raise RuntimeError("Database has not connected yet")
        return self.connection().cursor()

db = Database() #idk if this is okay it probably isn't should probably be context-specific

def generate_selector(argdict: dict):
    return ("WHERE "+" AND ".join([f"{k}={v}" for k,v in argdict.items() if not v == None])) if len(argdict) > 0 else ""