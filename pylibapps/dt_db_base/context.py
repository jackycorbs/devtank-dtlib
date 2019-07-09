import subprocess
from tests_group import tests_group_creator


class base_context_object(object):
    def __init__(self, args, fn_get_dev, work_folder, db_def):
        self.work_folder = work_folder
        self.db_def = db_def
        self.db = None
        self._fn_get_dev = fn_get_dev
        self.args = args
        self.devices = []
        self.on_exit_cbs = []
        self.tests_group = tests_group_creator(None)

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
            db = open_db_backend(self.db_def, self.work_folder)
        except Exception as e:
            print "ERROR database connection fail : %s" % str(e)
            db = None

        if db:
            self.db = db
            self.tests_group.db = db
            self.tests_group.update_defaults()
            from types import MethodType

            db.db.wake_fail_catch = MethodType(lambda db, e: \
                    self._db_fail(self, db, e), db.db, db.db.__class__)

            db.get_dev = types.MethodType(lambda db, uuid: \
                    self._fn_get_dev(db, uuid), db, db.__class__)
        return True

    def lock_bus(self):
        raise Exception("Context lock_bus not implimented.");

    def release_bus(self):
        raise Exception("Context release_bus not implimented.");

    def _db_fail(self, db, e):
        print "Failed to reconnect to database, %s" % str(e)
