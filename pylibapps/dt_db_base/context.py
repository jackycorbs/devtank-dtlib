import os
import subprocess
from tests_group import tests_group_creator

class base_context_object(object):
    def __init__(self, args, db_def):
        self.db_def = db_def
        self.db = None
        self.db_error = False
        self.args = args
        self.devices = []
        self.on_exit_cbs = []
        self.tests_group = tests_group_creator(None)
        assert "open_db_backend" in db_def
        assert "work_folder" in db_def
        assert "fn_get_dev" in db_def

    def close_app(self):
        for cb in self.on_exit_cbs:
            cb()

    def db_init(self):
        if self.db:
            return True

        host = self.db_def.get("host", None)
        if host:
            with open(os.devnull, 'w') as FNULL:
                has_error = subprocess.call("ping -W 1 -c 1 " + host,
                                            shell=True, stdout=FNULL,
                                            stderr=subprocess.STDOUT)
                if has_error:
                    print "Unable to ping host."
                    return False

        try:
            db = self.db_def["open_db_backend"](self.db_def)
        except Exception as e:
            print "ERROR database connection fail : %s" % str(e)
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
        from types import MethodType

        db.db.error_handler = lambda e: self._db_fail(e)

        db.get_dev = MethodType(lambda db, uuid: \
                get_dev(db, uuid), db, db.__class__)
        return True

    def lock_bus(self):
        raise Exception("Context lock_bus not implemented.");

    def release_bus(self):
        raise Exception("Context release_bus not implemented.");

    def _db_fail(self, e):
        print "Failed to reconnect to database, %s" % str(e)
        self.db = None
        self.db_error = True
