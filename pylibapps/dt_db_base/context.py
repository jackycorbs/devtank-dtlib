from __future__ import print_function, absolute_import

import os
import sys
import subprocess

from .tests_group import tests_group_creator


class base_context_object(object):
    def __init__(self, args, db_def):
        self.db_def = db_def
        self.db = None
        self.db_error = False
        self.args = args
        self.devices = []
        self.on_exit_cbs = []
        self.tests_group = tests_group_creator(None)
        self._in_db_init = False
        self._resource_dir = self.resource_dir
        resource_dir = self._resource_dir 
        assert "open_db_backend" in db_def
        assert "work_folder" in db_def
        assert "fn_get_dev" in db_def

    @property
    def resource_dir(self):
        return os.path.join(os.path.split(os.path.dirname(sys.argv[0]))[0], "resources")

    def close_app(self):
        for cb in self.on_exit_cbs:
            cb()

    def _db_init(self):
        if self.db:
            return True

        host = self.db_def.get("host", None)
        if host:
            with open(os.devnull, 'w') as FNULL:
                has_error = subprocess.call("ping -W 1 -c 1 " + host,
                                            shell=True, stdout=FNULL,
                                            stderr=subprocess.STDOUT)
                if has_error:
                    print("Unable to ping host.")
                    return False

        try:
            db = self.db_def["open_db_backend"](self)
        except Exception as e:
            print("ERROR database connection fail : %s" % str(e))
            import traceback
            traceback.print_exc()
            db = None
            self._db_fail(e)

        if not db:
            return False

        self.db = db
        self.db_error = False
        self.tests_group.db = db
        self.tests_group.update_defaults()
        get_dev = self.db_def["fn_get_dev"]
        get_dev_by_sn = self.db_def.get("fn_get_dev_by_sn", None)
        from types import MethodType

        db.db.error_handler = lambda e: self._db_fail(e)

        if sys.version_info[0] < 3:
            db.get_dev = MethodType(lambda db, uuid: \
                        get_dev(db, uuid), db, db.__class__)
            if get_dev_by_sn:
                db.get_dev_by_sn = MethodType(lambda db, serial_number: \
                        get_dev_by_sn(db, serial_number), db, db.__class__)
        else:
            db.get_dev = MethodType(lambda db, uuid: \
                        get_dev(db, uuid), db)
            if get_dev_by_sn:
                db.get_dev_by_sn = MethodType(lambda db, serial_number: \
                        get_dev_by_sn(db, serial_number), db)
        return True

    def db_init(self):
        if self._in_db_init:
            return None
        self._in_db_init = True
        r = self._db_init()
        self._in_db_init = False
        return r

    def lock_bus(self):
        raise NotImplementedError

    def release_bus(self):
        raise NotImplementedError

    def _db_fail(self, e):
        print("Fail with database, %s" % str(e))
        import traceback
        traceback.print_exc()
        self.db = None
        self.db_error = True
