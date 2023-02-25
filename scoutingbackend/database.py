import contextvars
import os
import sqlite3

import flask
import werkzeug.local

#THIS IS REALLY MESSY AND SHOULD BE FIXED

class Database(object):
    def connect(self, location: os.PathLike | str) -> None:
        self.loc = location
        #self.conn = sqlite3.connect(location)
        
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
    
    def commit(self):
        if not hasattr(self, 'loc'):
            raise RuntimeError("Database has not connected yet")
        self.connection().commit()

db = Database() #idk if this is okay it probably isn't should probably be context-specific