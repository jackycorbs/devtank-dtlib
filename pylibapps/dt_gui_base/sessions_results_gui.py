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
            self._on_row_double_click(model[treeiter][3])
            return

    def _on_row_double_click(self, session):
        self.context.tests_group.populate_from(session.group)
        self._size = None
        self._on_open_ran_view(session)


    def _on_open_ran_view(self, session):
        raise Exception("Unimplemented")

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
        lines_to_get /= float(self.line_height + self.line_space)

        if frac < 0.99:
            lines_to_get = int(math.ceil(lines_to_get))
        else:
            lines_to_get = int(lines_to_get)

        list_store = self.session_list_store

        append = True

        if self.prev_offset >= 0:
            delta = offset - self.prev_offset
            count = list_store.iter_n_children()

            if delta == 0:
                return
            elif delta > 0:
                if delta >= count:
                    list_store.clear()
                else:
                    lines_to_get = delta
                    while delta:
                        list_store.remove(list_store.get_iter_first())
                        delta -= 1
            else:
                delta = abs(delta)
                if delta >= count:
                    list_store.clear()
                else:
                    lines_to_get = delta
                    append = False
                    last_index = count - 1
                    while delta:
                        it = list_store.iter_nth_child(None, last_index)
                        list_store.remove(it)
                        last_index -= 1
                        delta -= 1
        else:
            list_store.clear()

        total_height =  self.header_height + (self.results_count * (self.line_height + self.line_space))

        self.session_results_pos.move(self.session_list, 0, pos)

        self.session_list.set_size_request(h_page_size, total_height - pos)

        if self.db_dev:
            results = self.db_dev.get_results(offset,
                      min(lines_to_get,
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
                                min(lines_to_get,
                                    self.results_count - offset))
            self.session_lab.set_text(
                "Results for Test Group\n\"%s\"" % tests_group.name)

        if not append:
            sessions.reverse()

        for session in sessions:
            stamp = datetime.datetime.fromtimestamp(session.time_of_tests)
            icon = get_pass_fail_icon_name(session.pass_fail)
            row = [str(stamp), session.group.name, icon, session]

            if append:
                list_store.append(row)
            else:
                list_store.insert(0, row)

        self.prev_offset = offset


    def _on_show(self):

        if self.db_dev:
            self.results_count = self.db_dev.get_results_count()
        else:
            tests_group = self.context.tests_group
            self.results_count = tests_group.db_group.get_sessions_count()

        # Get again incase of theme change.
        self.line_height = self.columns[0].cell_get_size().height
        self.header_height = max([size.height for size in
            self.columns[0].get_button().get_preferred_size() ])
        self.line_space = self.session_list.style_get_property("vertical-separator")

        self.adj.set_step_increment(self.line_height)
        self.prev_offset = -1


    def open(self, db_dev=None):
        self.db_dev = db_dev
        self.context.push_view()
        self.context.change_view("SessionResults")
