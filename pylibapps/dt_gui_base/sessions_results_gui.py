import datetime
import math

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GObject

from common import get_pass_fail_icon_name



class base_session_results_singlton(object):
    def __init__(self, context):
        self.context = context
        self.session_list = context.builder.get_object("session_results_list")
        self.session_lab = context.builder.get_object("results_lab")
        self.session_results_scroll = context.builder.get_object("session_results_scroll")
        self.session_results_pos = context.builder.get_object("session_results_pos")

        self.session_list_store = Gtk.ListStore(str, str, str, object)

        self.columns = [ Gtk.TreeViewColumn("Session",
                                            Gtk.CellRendererText(),
                                            text=0),
                         Gtk.TreeViewColumn("Test Group",
                                            Gtk.CellRendererText(),
                                            text=1),
                         Gtk.TreeViewColumn("Status",
                                             Gtk.CellRendererPixbuf(),
                                             icon_name=2) ]

        self.session_list.set_model(self.session_list_store)
        self.session_list.append_column(self.columns[0])
        self.session_list.append_column(self.columns[1])
        self.session_list.append_column(self.columns[2])

        self.line_height = self.columns[0].cell_get_size().height
        self.header_height = max([size.height for size in
            self.columns[0].get_button().get_preferred_size() ])
        self.line_space = self.session_list.style_get_property("vertical-separator")

        back_btn = context.builder.get_object("results_back_btn")
        window = context.builder.get_object("SessionResults")

        back_btn.connect("clicked", lambda btn: self._on_back())
        window.connect("show", lambda x: self._on_show())
        self.db_dev = None

        ok_btn = context.builder.get_object("results_ok_btn")
        ok_btn.connect("clicked", lambda btn: self._on_ok())

        self.session_list.connect("row-activated", lambda treeview, path, column: \
            self._on_row_double_click(treeview.get_model()[path][3]))

        self.adj = self.session_results_scroll.get_vadjustment()

        self.adj.connect("value-changed", lambda adj : self._scroll_change())

        self.results_count = 0


    def _on_ok(self):
        selection = self.session_list.get_selection()
        model = self.session_list.get_model()
        treeiters = selection.get_selected_rows()[1]
        for treeiter in treeiters:
            self._on_row_double_click(model[treeiter][3])
            return

    def _on_row_double_click(self, session):
        self.context.tests_group.populate_from(session.group)
        self._on_open_ran_view(session)


    def _on_open_ran_view(self, session):
        raise Exception("Unimplemented")

    def _on_back(self):
        self.context.pop_view()

    def _scroll_change(self):
        value = self.adj.get_value()
        limit = self.adj.get_upper() - self.adj.get_page_size()
        frac = value / limit

        self.session_results_pos.move(self.session_list, 0, int(value))

        offset = int(self.results_count * frac)

        self._update_view(offset)


    def _update_view(self, offset):
        hadj = self.session_results_scroll.get_hadjustment()

        total_height =  self.header_height + (self.results_count * (self.line_height + self.line_space))
        self.session_list.set_size_request(hadj.get_page_size(), total_height)

        self.session_list_store.clear()

        visable_lines = self.adj.get_page_size() - self.header_height
        visable_lines /= float(self.line_height + self.line_space)
        visable_lines = int(math.ceil(visable_lines))

        if self.db_dev:
            results = self.db_dev.get_results(offset,
                      min(visable_lines,
                          self.results_count - offset))
            sessions = []
            for v in results['Pass'] + results['Fail']:
                sessions += [ v['session_id'] ]
            if len(sessions):
                sessions = self.context.db.get_sessions(sessions)
            self.session_lab.set_text(
                "Results for Device\n\"%s\"" % (self.db_dev.uuid))
        else:
            tests_group = self.context.tests_group
            sessions = tests_group.db_group.get_sessions(offset,
                                min(visable_lines,
                                    self.results_count - offset))
            self.session_lab.set_text(
                "Results for Test Group\n\"%s\"" % tests_group.name)

        for session in sessions:
            stamp = datetime.datetime.fromtimestamp(session.time_of_tests)
            icon = get_pass_fail_icon_name(session.pass_fail)
            self.session_list_store.append(
                [str(stamp), session.group.name, icon, session])

    def _on_show(self):

        if self.db_dev:
            self.results_count = self.db_dev.get_results_count()
        else:
            tests_group = self.context.tests_group
            self.results_count = tests_group.db_group.get_sessions_count()

        self._update_view(0)



    def open(self, db_dev=None):
        self.db_dev = db_dev
        self.context.push_view()
        self.context.change_view("SessionResults")
