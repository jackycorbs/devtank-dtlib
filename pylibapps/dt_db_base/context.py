import subprocess
from tests_group import tests_group_creator

class base_context_object(object):
    def __init__(self, args, db_def):
        self.db_def = db_def
        self.db = None
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
                    return True

        try:
            db = self.db_def["open_db_backend"](self.db_def)
        except Exception as e:
            print "ERROR database connection fail : %s" % str(e)
            db = None
            self._db_fail(e)

        if db:
            self.db = db
            self.tests_group.db = db
            self.tests_group.update_defaults()
            from types import MethodType

            db.db.fail_catch = MethodType(lambda e: \
                    self._db_fail(self, e), db.db, db.db.__class__)

            db.get_dev = MethodType(lambda db, uuid: \
                    self.db_def["fn_get_dev"](db, uuid), db, db.__class__)
        return True

    def lock_bus(self):
        raise Exception("Context lock_bus not implimented.");

    def release_bus(self):
        raise Exception("Context release_bus not implimented.");

    def _db_fail(self, e):
        print "Failed to reconnect to database, %s" % str(e)
