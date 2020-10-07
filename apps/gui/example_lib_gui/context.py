import example_lib

from dt_gui_base import gui_context_object as base_gui_context_object


class gui_context_object(base_gui_context_object):
    def __init__(self, args, db_def, builder):
        base_gui_context_object.__init__(self, args, db_def, builder)
        self.__bus = example_lib.example_bus()
        self.locked = False
        self.db_dev = None

    def lock_bus(self):
        if self.locked:
            return None
        self.locked = True
        return self.__bus

    def release_bus(self):
        self.locked = False

    def _db_fail(self, e):
        base_gui_context_object._db_fail(self, e)
        from .start_gui import open_start_page
        self.clear_view_stack()
        open_start_page(self)
