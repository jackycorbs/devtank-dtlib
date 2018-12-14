
from tests_group import tests_group_creator


class base_context_object(object):
    def __init__(self, args, db):
        self.db = db
        self.args = args
        self.devices = []
        self.on_exit_cbs = []
        self.tests_group = tests_group_creator(db)

    def close_app(self):
        for cb in self.on_exit_cbs:
            cb()

    def lock_bus(self):
        raise Exception("Context lock_bus not implimented.");

    def release_bus(self):
        raise Exception("Context release_bus not implimented.");
