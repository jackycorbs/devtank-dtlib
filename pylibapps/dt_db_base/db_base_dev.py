import sys

from .db_common import db_time
from .db_obj import db_child
from .db_tests import test_group_sessions


class db_base_dev(db_child):
    def __init__(self,
                 db,
                 serial_number,
                 dev_db_id,
                 uuid):
        db_child.__init__(self, db, db_id=dev_db_id, db_serial=serial_number, db_extras={"uuid" : uuid})
        self.uuid = uuid

    @staticmethod
    def _get_by_serial(dev_class, db, serial_number):
        return db_child._get_by_serial(db, dev_class,
                                        db.sql.get_dev_by_serial,
                                        serial_number)

    @staticmethod
    def _get_by_id(dev_class, db, dev_id):
        return db_child._get_by_id(db, dev_class,
                                    db.sql.get_dev_by_id,
                                    dev_id)

    @staticmethod
    def _get_by_uuid(dev_class, db, uuid):
        return db_child._get_by_extra(db, dev_class,
                                    "uuid",
                                    db.sql.get_dev_by_uid,
                                    uuid)

    @staticmethod
    def get_dev_status_since(db, timestamp):
        cmd = db.sql.get_dev_status_since(db_time(timestamp))
        rows = db.db.query(cmd)
        r = {}
        for row in rows:
            dev_uid, group_name, test_time, pass_fail = row
            r.setdefault(dev_uid, {})
            r[dev_uid][group_name] = (test_time, pass_fail)
        return r

    def get_session_count(self):
        cmd = self.db.sql.get_dev_session_count(self.id)
        rows = self.db.db.query(cmd)
        return rows[0][0]

    def get_sessions(self, offset, count):
        cmd = self.db.sql.get_dev_sessions(self.id, offset, count)
        rows = self.db.db.query(cmd)
        return [ test_group_sessions(self.db.get_group_by_id(row[2]),
                                     self.db, row[0], row[1], row[3], row[4]) \
                 for row in rows ]

    def update_uuid(self, new_uuid):
        cmd = self.db.sql.get_update_dev_uid(self.id, new_uuid)
        self.db.db.update(cmd)
        self.uuid = new_uuid

    def get_last_result(self, group_name, do_like=False):
        cmd = self.db.sql.get_dev_last_result(self.id, group_name, do_like)
        row = self.db.db.query_one(cmd)
        if row is None:
            return None
        return bool(row[1])

    def get_last_session(self, group_name):
        cmd = self.db.sql.get_dev_last_session(self.id, group_name)
        row = self.db.db.query_one(cmd)
        if row is None:
            return None
        return test_group_sessions(self.db.get_group_by_id(row[2]),
                                   self.db, row[0], row[1], row[3], row[4])
