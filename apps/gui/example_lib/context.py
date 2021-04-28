from __future__ import print_function, absolute_import

from .example_hw import example_bus

from dt_db_base import base_context_object


class cli_context_object(base_context_object):
    def __init__(self, args, db_def):
        base_context_object.__init__(self, args, db_def)
        self.__bus = example_bus()
        self.locked = False
        self.db_dev = None

    def lock_bus(self):
        if self.locked:
            return None
        self.locked = True
        return self.__bus

    def release_bus(self):
        self.locked = False
