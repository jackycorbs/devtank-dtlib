import os
import sqlite3
import datetime
from database import tester_database
from db_filestore_protocol import sftp_transferer
from db_inf import db_inf


class sqlite_tester_database(tester_database):
    def __init__(self, db, sql, work_folder):
        tester_database.__init__(self, db, sql, work_folder)

    def get_db_now():
        return datetime.datetime.utcnow()



class sqlite_db_backend(object):
    def __init__(self, db_def):
        self.db_def = db_def


    def open(self, work_folder):
        filename = self.db_def["filename"]
        return sqlite_tester_database(db_inf(sqlite3.connect(filename)),
                                      self.db_def["sql"],
                                      work_folder)

    def is_empty(self):
        filename = self.db_def["filename"]
        return not os.path.exists(filename)


    def load(self, schema):
        filename = self.db_def["filename"]
        if os.path.exists(filename):
            os.remove(filename)

        filestore_dir = os.path.abspath(self.db_def['db_files']);

        if not os.path.exists(filestore_dir):
            os.mkdir(filestore_dir)

        db = sqlite3.connect(filename)

        for s in schema:
            s = s.strip()
            if len(s):
                try:
                    db.execute(s)
                except Exception as e:
                    raise Exception('Failed to do SQL "%s" : %s' % (s, str(e)))
        db.commit()

        self.db_def['file_stores'] = { "sftp": [ ["localhost", filestore_dir] ] }
        db.close()
