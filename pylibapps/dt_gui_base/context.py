import gi
import sys
import os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

from dt_db_base import base_context_object, int_logging

class gui_context_object(base_context_object):
    def __init__(self, args, db_def, glade_files):
        self._logger = int_logging.get_logger(__name__)
        base_context_object.__init__(self, args, db_def)

        resource_dir = self.resource_dir

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(resource_dir, 'gui_base.glade'))
        for glade_file in glade_files:
            builder.add_from_file(os.path.join(resource_dir, glade_file))

        self.current_view = None
        self.builder = builder
        self.good_icon = GdkPixbuf.Pixbuf.new_from_file(os.path.join(resource_dir, "good.svg")).scale_simple(20, 20, GdkPixbuf.InterpType.BILINEAR)
        self.bad_icon  = GdkPixbuf.Pixbuf.new_from_file(os.path.join(resource_dir,  "bad.svg")).scale_simple(20, 20, GdkPixbuf.InterpType.BILINEAR)
        self.prev_view = []
        self.view_objs = {}

    def get_pass_fail_icon_name(self, passfail):
        return self.good_icon if passfail else self.bad_icon

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
        self._logger.debug(f"VIEW SET {name}")
        self.print_view_stack()
        view_obj = self.view_objs.get(name, None)
        if view_obj:
            self.current_view = name
            view_obj.show_view()
        else:
            self.force_view(name)
            self.current_view = name

    def close_app(self):
        base_context_object.close_app(self)
        Gtk.main_quit()

    def push_view(self):
        self._logger.debug(f"VIEW PUSH {self.current_view}")
        self.prev_view += [ self.current_view ]

    def print_view_stack(self):
        l = len(self.prev_view)
        for n in range(0, l):
            view = self.prev_view[l-n-1]
            self._logger.debug(f"VIEW STACK [%u]: {view}" % n)

    def pop_view(self):
        prev_view = self.prev_view.pop()
        self._logger.debug(f"VIEW POP {prev_view}")
        if prev_view:
            self.change_view(prev_view)

    def drop_view(self):
        self.prev_view.pop()
        self._logger.debug(f"VIEW POP {prev_view}")

    def clear_view_stack(self):
        self.prev_view = []
        self._logger.debug("VIEW STACKED CLEARED")
