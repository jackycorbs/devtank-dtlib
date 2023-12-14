import os
import sys
import time
import pymssql

from .database import tester_database
from .db_filestore_protocol import smb_transferer
from .db_inf import db_inf

_MSSQL_AUTO_DISCONNECT = 60 * 5


class login_smb_transferer(smb_transferer):
    def __init__(self, db_def):
        smb_transferer.__init__(self)
        self.username = db_def['user']
        self.password = db_def['password']
        self.domain = None
        devider = self.username.find('\\')
        if devider > 0:
            self.domain = self.username[0:devider]
            self.username = self.username[devider+1:]

    def _get_smb_username(self):
        return self.username

    def _get_smb_password(self):
        return self.password

    def _get_smb_domain(self):
        return self.domain

#mssql_tester_database class untested/unmaintained
class mssql_tester_database(tester_database):
    def __init__(self, db, work_folder, db_def):
        tester_database.__init__(self, db, db_def['sql'], work_folder)
        self.protocol_transferers[smb_transferer.protocol_id] = login_smb_transferer(db_def)

    def get_db_now():
        row = self.db.query_one("SELECT GETUTCDATE()")
        return row[0]


def _do_raw_connect(db_def):
    return pymssql.connect( host=db_def['host'],
                            port=db_def['port'],
                            user=db_def['user'],
                            login_timeout=4,
                            password=db_def['password'],
                            appname=db_def['appname'],
                            tds_version=db_def['tds_version'],
                            database=db_def['database'])


class mssql_db_inf(db_inf):
    def __init__(self, db_def):
        db_inf.__init__(self,
                        db_def,
                        _do_raw_connect,
                        _MSSQL_AUTO_DISCONNECT)


class mssql_db_backend(object):
    def __init__(self, db_def):
        self.db_def = db_def

    def open_raw_db(self):
        db_def = self.db_def
        return pymssql.connect( host=db_def['host'],
                                port=db_def['port'],
                                user=db_def['user'],
                                login_timeout=4,
                                password=db_def['password'],
                                appname=db_def['appname'],
                                tds_version=db_def['tds_version'],
                                database=db_def['database'])

    def open(self, work_folder):
        db = mssql_db_inf(self.db_def)
        return mssql_tester_database(db, work_folder, self.db_def)


    def is_empty(self):
        db = self.open_raw_db()

        c = db.cursor()
        c.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES")

        rows = c.fetchall()

        return not len(rows)


    def load(self, schema):
        db = self.open_raw_db()

        c = db.cursor()

        for s in schema:
            s = s.strip()
            if len(s):
                s = s.replace("AUTOINCREMENT", "IDENTITY(1,1)")
                try:
                    c.execute(s)
                except Exception as e:
                    raise Exception('Failed to do SQL "%s" : %s' % (s, str(e)))

        db.commit()
        db.close()
