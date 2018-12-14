import os
import psycopg2
import pytz
from database import tester_database
from db_filestore_protocol import sftp_transferer
from db_inf import db_inf, db_cursor



class pg_db_cursor(db_cursor):
    def __init__(self, parent):
        db_cursor.__init__(self, parent)

    def insert(self, cmd):
        self._execute(cmd + " RETURNING id")
        return self._c.fetchone()[0]


class pg_db_inf(db_inf):
    def __init__(self, db):
        db_inf.__init__(self, db)

    def cursor(self):
        return pg_db_cursor(self)



class pg_tester_database(tester_database):
    def __init__(self, db, sql, work_folder):
        tester_database.__init__(self, db, sql, work_folder)

    def get_db_now():
        row = self.db.query_one("SELECT CAST(CURRENT_TIMESTAMP AS TIMESTAMPTZ)")
        return row[0].astimezone(pytz.utc)



class pg_db_backend(object):
    def __init__(self, db_def):
        self.db_def = db_def


    def open_raw(self):
        db_def = self.db_def
        return psycopg2.connect( "dbname=%s "\
                                 "user=%s "\
                                 "password=%s "\
                                 "host=%s" % (db_def["dbname"],
                                              db_def["user"],
                                              db_def["password"],
                                              db_def["host"]))

    def open(self, work_folder):
        db = self.open_raw()
        return pg_tester_database(pg_db_inf(db), self.db_def['sql'], work_folder)


    def is_empty(self):
        db = self.open_raw()
        c = db.cursor()
        cmd = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        c.execute(cmd)
        rows = c.fetchall()

        return not len(rows)


    def load(self, schema):
        db = self.open_raw()

        c = db.cursor()

        for s in schema:
            s = s.strip()
            if len(s):
                s = s.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
                try:
                    c.execute(s)
                except Exception as e:
                    raise Exception('Failed to do SQL "%s" : %s' % (s, str(e)))

        db.commit()
        db.close()
