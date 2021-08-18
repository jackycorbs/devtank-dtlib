from __future__ import print_function, absolute_import

import datetime
import math
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GObject, GdkPixbuf


class base_session_results_singlton(object):
    def __init__(self, context):
        self.context = context
        self.session_list = context.builder.get_object("session_results_list")
        self.session_lab = context.builder.get_object("results_lab")
        self.session_results_scroll = context.builder.get_object("session_results_scroll")
        self.session_results_pos = context.builder.get_object("session_results_pos")

        self.session_list_store = Gtk.ListStore(str, str, GdkPixbuf.Pixbuf, str, str, object)

        self.columns = [ Gtk.TreeViewColumn("Session",
                                            Gtk.CellRendererText(),
                                            text=0),
                         Gtk.TreeViewColumn("Test Group",
                                            Gtk.CellRendererText(),
                                            text=1),
                         Gtk.TreeViewColumn("Status",
                                             Gtk.CellRendererPixbuf(),
                                             pixbuf=2),
                         Gtk.TreeViewColumn("Devs",
                                            Gtk.CellRendererText(),
                                            text=3),
                         Gtk.TreeViewColumn("Test Machine",
                                            Gtk.CellRendererText(),
                                            text=4),
                          ]

        self.session_list.set_model(self.session_list_store)
        for column in self.columns:
            self.session_list.append_column(column)

        line_space = self.session_list.style_get_property("vertical-separator")
        self.line_height = self.columns[0].cell_get_size().height + (line_space * 2)
        self.header_height = max([size.height for size in
            self.columns[0].get_button().get_preferred_size() ])

        back_btn = context.builder.get_object("results_back_btn")
        window = context.builder.get_object("SessionResults")

        back_btn.connect("clicked", lambda btn: self._on_back())
        window.connect("show", lambda x: self._on_show())
        self.db_dev = None

        ok_btn = context.builder.get_object("results_ok_btn")
        ok_btn.connect("clicked", lambda btn: self._on_ok())

        self.session_list.connect("row-activated", lambda treeview, path, column: \
            self._on_row_double_click(treeview.get_model()[path][-1]))

        self._size = None
        self.session_results_scroll.connect("size-allocate", lambda w, r : self._on_resize(r))

        self.adj = self.session_results_scroll.get_vadjustment()

        self.adj.connect("value-changed", lambda adj : self._update_view())

        self.results_count = 0
        self.prev_offset = -1


    def _on_ok(self):
        selection = self.session_list.get_selection()
        model = self.session_list.get_model()
        treeiters = selection.get_selected_rows()[1]
        for treeiter in treeiters:
            self._on_row_double_click(model[treeiter][-1])
            return

    def _on_row_double_click(self, session):
        self.context.tests_group.populate_from(session.group, session.time_of_tests)
        self._size = None
        self._on_open_ran_view(session)


    def _on_open_ran_view(self, session):
        from .base_group_run_gui import open_ran_group
        open_ran_group(self.context, session)

    def _on_back(self):
        self._size = None
        self.context.pop_view()

    def _on_resize(self, r):
        old_r = self._size
        if old_r is None or old_r[0] != r.width or old_r[1] != r.height:
            self._size = (r.width, r.height)
            self.prev_offset = -1
            self._update_view()

    def _update_view(self):
        value = self.adj.get_value()
        limit = self.adj.get_upper()
        frac = value / limit

        offset = int(self.results_count * frac)
        pos    = int(value)

        h_page_size = self.session_results_scroll.get_hadjustment().get_page_size()
        v_page_size = self.adj.get_page_size()

        lines_to_get = v_page_size - self.header_height
        lines_to_get /= float(self.line_height)

        lines_to_get = int(lines_to_get)

        list_store = self.session_list_store

        list_store.clear()

        total_height =  self.header_height + ((self.results_count + 2) * self.line_height)

        # The maths isn't exact, and it can make it hard to get to the end, or so you can go past it.
        # This stops you going past the end and makes sure the end really is the end.
        if (pos + v_page_size) >= total_height:
            pos = total_height - v_page_size
            if (offset + lines_to_get) < (self.results_count - 1):
                offset = self.results_count - 1 - lines_to_get
                if offset < 0:
                    offset = 0
            if pos < 0:
                pos = 0

        self.session_results_pos.move(self.session_list, 0, pos)
        self.session_results_pos.set_size_request(h_page_size, total_height)

        self.session_list.set_size_request(h_page_size, v_page_size)

        if self.db_dev:
            sessions = self.db_dev.get_sessions(offset, lines_to_get)
            self.session_lab.set_text(
                "Results for Device\n\"%s\"" % (self.db_dev.uuid))
        else:
            tests_group = self.context.tests_group
            sessions = tests_group.db_group.get_all_sessions(offset, lines_to_get)
            self.session_lab.set_text(
                "Results for Test Group\n\"%s\"" % tests_group.name)

        sessions.reverse()

        for session in sessions:
            devs = session.dev_serials
            stamp = datetime.datetime.fromtimestamp(session.time_of_tests)
            icon = self.context.get_pass_fail_icon_name(session.pass_fail)
            machine = session.get_tester_line_str()

            row = [stamp.strftime("%Y-%m-%d %H:%M:%S"), session.group.name, icon, ",".join(devs), machine, session]
            list_store.insert(0, row)


    def _on_show(self):

        if self.db_dev:
            self.results_count = self.db_dev.get_session_count()
        else:
            tests_group = self.context.tests_group
            self.results_count = tests_group.db_group.get_all_sessions_count()

        # Get again incase of theme change.
        self.header_height = max([size.height for size in
            self.columns[0].get_button().get_preferred_size() ])
        line_space = self.session_list.style_get_property("vertical-separator")
        self.line_height = self.columns[0].cell_get_size().height + (line_space * 2)

        self.adj.set_step_increment(self.line_height)
        self.prev_offset = -1


    def open(self, db_dev=None):
        self.db_dev = db_dev
        self.context.push_view()
        self.context.change_view("SessionResults")

_session_results = None


def open_tests_sessions_results(context):
    global _session_results
    _session_results.open()

def open_dev_tests_sessions_results(context, db_dev):
    global _session_results
    assert db_dev
    _session_results.open(db_dev)

def init_tests_sessions_results(context):
    global _session_results
    _session_results = base_session_results_singlton(context)
