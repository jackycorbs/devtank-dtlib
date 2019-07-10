import os
import time
import mysql.connector as mysqlconn
import pytz
from database import tester_database
from db_filestore_protocol import sftp_transferer
from db_inf import db_inf, db_cursor

_MYSQL_AUTO_DISCONNECT = 60 * 5


class mysql_db_cursor(db_cursor):
    def __init__(self, parent):
        db_cursor.__init__(self, parent)

    def insert(self, cmd):
        self._execute(cmd)
        ret = self._c.lastrowid
        return ret


def _do_raw_connect(db_def):
    return mysqlconn.connect(database=db_def["dbname"],
                             user=db_def["user"],
                             password=db_def["password"],
                             host=db_def["host"],
                             port=db_def.get("port", 3306),
                             sql_mode='ANSI_QUOTES')


class mysql_db_inf(db_inf):
    def __init__(self, db_def):
        db_inf.__init__(self,
                        db_def,
                        _do_raw_connect,
                        _MYSQL_AUTO_DISCONNECT)

    def cursor(self):
        return mysql_db_cursor(self)

    


class mysql_tester_database(tester_database):
    def __init__(self, db, sql, work_folder, db_def):
        tester_database.__init__(self, db, sql, work_folder)
        self.protocol_transferers = {sftp_transferer.protocol_id : sftp_transferer(db_def) }

    def get_db_now():
        row = self.db.query_one("SELECT NOW()")
        return row[0].astimezone(pytz.utc)


class mysql_db_backend(object):
    def __init__(self, db_def):
        self.db_def = db_def

    def open(self, work_folder):
        return mysql_tester_database(mysql_db_inf(self.db_def),
                                     self.db_def['sql'],
                                     work_folder,
                                     self.db_def)

    def is_empty(self):
        db = _do_raw_connect(self.db_def)
        c = db.cursor()
        cmd = "SELECT table_name FROM information_schema.tables WHERE table_schema = '" + self.db_def["dbname"] + "'"
        c.execute(cmd)
        rows = c.fetchall()
        return not len(rows)

    def load(self, schema):
        db = _do_raw_connect(self.db_def)

        c = db.cursor()

        for s in schema:
            s = s.strip()
            if len(s):
                s = s.replace("AUTOINCREMENT", "AUTO_INCREMENT")
                try:
                    c.execute(s)
                except Exception as e:
                    raise Exception('Failed to do SQL "%s" : %s' % (s, str(e)))

        db.commit()
        db.close()
