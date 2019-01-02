import datetime

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from common import get_pass_fail_icon_name



class base_session_results_singlton(object):
    def __init__(self, context):
        self.context = context
        self.session_list = context.builder.get_object("session_results_list")
        self.session_lab = context.builder.get_object("results_lab")
        self.session_hscroll = context.builder.get_object("results_hscroll")

        self.session_list_store = Gtk.ListStore(str, str, str, object)

        self.session_list.set_model(self.session_list_store)
        self.session_list.append_column(
            Gtk.TreeViewColumn("Session", Gtk.CellRendererText(), text=0))
        self.session_list.append_column(
            Gtk.TreeViewColumn("Test Group", Gtk.CellRendererText(), text=1))
        self.session_list.append_column(
            Gtk.TreeViewColumn("Status", Gtk.CellRendererPixbuf(), icon_name=2))

        back_btn = context.builder.get_object("results_back_btn")
        window = context.builder.get_object("SessionResults")

        back_btn.connect("clicked", lambda btn: self._on_back())
        window.connect("show", lambda x: self._on_show())
        self.db_dev = None

        ok_btn = context.builder.get_object("results_ok_btn")
        ok_btn.connect("clicked", lambda btn: self._on_ok())

        self.session_list.connect("row-activated", lambda treeview, path, column: \
            self._on_row_double_click(treeview.get_model()[path][3]))

        self.session_hscroll.set_increments(100, 100)
        self.session_hscroll.connect("move-slider", lambda range, step: \
            self._on_hscroll())
        self.session_hscroll_max = 0


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

    def _on_hscroll(self):
        pos = self.session_hscroll.get_value()
        self._update_view(int(pos))

    def _update_view(self, offset):
        self.session_list_store.clear()

        if self.db_dev:
            results       = self.db_dev.get_results(offset,
                      min(100, self.session_hscroll_max - offset))
            sessions = []
            for v in results['Pass'] + results['Fail']:
                sessions += [ v['session_id'] ]
            if len(sessions):
                sessions = self.context.db.get_sessions(sessions)
            self.session_lab.set_text(
                "Results for Device\n\"%s\"" % (self.db_dev.uuid))
        else:
            tests_group = self.context.tests_group
            sessions = tests_group.db_group.get_sessions(0,
                                min(100, self.session_hscroll_max - offset))
            self.session_lab.set_text(
                "Results for Test Group\n\"%s\"" % tests_group.name)

        session_map = dict([ (session.time_of_tests, session) \
                              for session in sessions ])

        session_dates = session_map.keys()
        session_dates.sort()

        for session_date in session_dates:
            session = session_map[session_date]
            stamp = datetime.datetime.fromtimestamp(session.time_of_tests)
            icon = get_pass_fail_icon_name(session.pass_fail)
            self.session_list_store.append(
                [str(stamp), session.group.name, icon, session])


    def _on_show(self):

        if self.db_dev:
            results_count = self.db_dev.get_results_count()
            self.session_hscroll.set_range(0, results_count)
            self.session_hscroll_max = results_count
        else:
            tests_group = self.context.tests_group
            sessions_count = tests_group.db_group.get_sessions_count()
            self.session_hscroll.set_range(0, sessions_count)
            self.session_hscroll_max = sessions_count

        self._update_view(0)


    def open(self, db_dev=None):
        self.db_dev = db_dev
        self.context.push_view()
        self.context.change_view("SessionResults")
