import gi
import sys
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from dt_db_base import base_context_object

class gui_context_object(base_context_object):
    def __init__(self, args, db_def, builder):
        base_context_object.__init__(self, args, db_def)
        self.current_view = None
        self.builder = builder
        self.prev_view = []
        self.view_objs = {}

    def force_view(self, name):
        builder = self.builder
        main_window = builder.get_object("main_window")
        next_view = builder.get_object(name)

        for child in main_window.get_children():
            main_window.remove(child)

        next_view.unparent()
        main_window.add(next_view)
        next_view.hide()
        next_view.show_all()
        if not self.args['desktop']:
            self.fullscreen()

    def fullscreen(self):
        main_window = self.builder.get_object("main_window")
        main_window.fullscreen()
        screen = main_window.get_screen()
        main_window.resize(screen.get_width(), screen.get_height())
        main_window.maximize()
        main_window.set_decorated(False)

    def change_view(self, name):
        view_obj = self.view_objs.get(name, None)
        if view_obj:
            self.current_view = name
            view_obj.show_view()
        else:
            self.force_view(name)
            self.current_view = name

    def close_app(self):
        base_context_object.close_app(self)
        sys.exit(0)

    def push_view(self):
        self.prev_view += [ self.current_view ]

    def pop_view(self):
        prev_view = self.prev_view.pop()
        if prev_view:
            self.change_view(prev_view)

    def drop_view(self):
        self.prev_view.pop()
