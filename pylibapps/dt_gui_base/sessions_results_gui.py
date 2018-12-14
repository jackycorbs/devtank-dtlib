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

    def _on_back(self):
        self.context.pop_view()


    def _on_show(self):

        self.session_list_store.clear()

        if self.db_dev:
            results = self.db_dev.get_latest_results()
            sessions = []
            for v in results['Pass'] + results['Fail']:
                sessions += [ v['session_id'] ]
            if len(sessions):
                sessions = self.context.db.get_sessions(sessions)
            self.session_lab.set_text(
                "Results for Device\n\"%s\"" % (self.db_dev.uuid))
        else:
            tests_group = self.context.tests_group
            sessions = tests_group.db_group.get_sessions()
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

    def open(self, db_dev=None):
        self.db_dev = db_dev
        self.context.push_view()
        self.context.change_view("SessionResults")
