import os
import sys
import sqlite3
import datetime

if sys.version_info[0] < 3:
    from database import tester_database
    from db_filestore_protocol import sftp_transferer
    from db_inf import db_inf
else:
    from .database import tester_database
    from .db_filestore_protocol import sftp_transferer
    from .db_inf import db_inf


class sqlite_tester_database(tester_database):
    def __init__(self, db, sql, work_folder):
        tester_database.__init__(self, db, sql, work_folder)

    def get_db_now():
        return datetime.datetime.utcnow()



def _do_raw_connect(db_def):
    return sqlite3.connect(db_def["filename"])


class sqlite_db_inf(db_inf):
    def __init__(self, db_def):
        db_inf.__init__(self, db_def, _do_raw_connect)

    def clean(self):
        pass



class sqlite_db_backend(object):
    def __init__(self, db_def):
        self.db_def = db_def

    def open(self, work_folder):
        return sqlite_tester_database(sqlite_db_inf(self.db_def),
                                      self.db_def["sql"],
                                      work_folder)

    def is_empty(self):
        filename = self.db_def["filename"]
        return not os.path.exists(filename)


    def load(self, schema):
        filestore_dir = os.path.abspath(self.db_def['db_files']);

        if not os.path.exists(filestore_dir):
            os.mkdir(filestore_dir)

        db = _do_raw_connect(self.db_def)

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
