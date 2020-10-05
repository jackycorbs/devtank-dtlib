import os
import time
import datetime
import sys

if sys.version_info[0] < 3:
    from common import get_pass_fail_icon_name
    from notify_gui import open_notify_gui
else:
    from .common import get_pass_fail_icon_name
    from .notify_gui import open_notify_gui

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango




class base_run_context(object):
    def __init__(self, context, run_group_manager_class):
        builder = context.builder

        self.context = context

        self.window = builder.get_object("TestGroupRunner")
        self.run_lab = builder.get_object("run_lab")

        self.run_lab.modify_font(Pango.FontDescription('Mono'))

        self.test_list = builder.get_object("RunTestsList")
        self.dev_list = builder.get_object("RunDevList")

        self.dev_list.set_model(Gtk.ListStore(str, str))
        self.dev_list.append_column(Gtk.TreeViewColumn("Device", Gtk.CellRendererText(), text=0))
        self.dev_list.append_column(Gtk.TreeViewColumn("Status", Gtk.CellRendererPixbuf(), icon_name=1))

        self.test_list.set_model(Gtk.ListStore(str, str, object))
        self.test_list.append_column(Gtk.TreeViewColumn("Test", Gtk.CellRendererText(), text=0))
        self.test_list.append_column(Gtk.TreeViewColumn("Status", Gtk.CellRendererPixbuf(), icon_name=1))

        self.run_cancel_btn = builder.get_object("run_cancel_btn")
        self.run_ok_btn = builder.get_object("run_ok_btn")
        self.info_btn = builder.get_object("run_info_btn")
        self.run_info = builder.get_object("run_info")
        self.redo_btn = builder.get_object("run_redo_btn")
        self.run_split_box = builder.get_object("run_split_box")

        self.out_text = builder.get_object("test_output_text")
        self.log_text = builder.get_object("test_log_text")

        is_desktop = True if context.args['desktop'] else False
        self.out_text.set_sensitive(is_desktop)
        self.log_text.set_sensitive(is_desktop)

        self.out_text.connect("size-allocate", self._scroll_to_end)
        self.log_text.connect("size-allocate", self._scroll_to_end)

        self.out_text.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))
        self.log_text.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))

        self.out_buf = self.out_text.get_buffer()
        self.log_buf = self.log_text.get_buffer()

        self.good_tag = self.out_buf.create_tag("good", foreground="#00FF00")
        self.bad_tag  = self.out_buf.create_tag("bad", foreground="#FF0000")
        self.norm_tag = self.out_buf.create_tag("norm", foreground="#FFFFFF")

        self.err_tag  = self.log_buf.create_tag("error", foreground="#FF0000")
        self.warn_tag = self.log_buf.create_tag("warn", foreground="#FFFF00")
        self.info_tag = self.log_buf.create_tag("info", foreground="#FFFFFF")

        self.run_group_man = run_group_manager_class(context,
            self._good_line,  self._bad_line,  self._normal_line,
            self._info_line,  self._warning_line,  self._error_line,
            {"FINISHED":      lambda args:     self.finished(),
             "SELECT_TEST":   lambda testfile: self.select_testfile(testfile),
             "SELECT_DEV" :   lambda dev_uuid: self.select_dev(dev_uuid),
             "START_OUTPUT":  lambda outfile:  self.start_outfile(outfile),
             "START_LOGFILE": lambda logfile:  self.start_logfile(logfile),
             "STATUS_TEST":   lambda args:     self.test_status(args),
             "STATUS_DEV":    lambda passfail: self.dev_status(passfail == "True"),
             "SET_UUID":      lambda new_uuid: self.dev_set_uuid(new_uuid)
            })

        self.total_duration = None
        self.progress_bar = builder.get_object("running_time")

        self.test_time = 0
        self.total_test_time = 0
        self.test_start_time = 0

        self.update_id = None

        self.run_cancel_btn.connect("clicked", lambda btn: self.on_cancel())
        self.run_ok_btn.connect("clicked",     lambda btn: self.on_ok())
        self.info_btn.connect("toggled",       lambda btn: self.on_info())
        self.redo_btn.connect("clicked",       lambda btn: self.on_redo())

        context.on_exit_cbs.insert(0, self.force_stop)

        selection = self.dev_list.get_selection()
        selection.connect("changed", lambda sel : self.select_dev_list())

        selection = self.test_list.get_selection()
        selection.connect("changed", lambda sel : self.load_info())

        context.view_objs["RunGroupViewObj"] = self


    def show_view(self):

        self.context.force_view("TestGroupRunner")

        self.info_btn.set_active(False)
        self.run_info.set_visible(False)

        if not self.run_group_man.readonly:
            self.start_test_group()

    def update_status_time(self):
        if not self.run_group_man.live:
            self._stop_update()
            self.test_list.set_sensitive(True)
            self.dev_list.set_sensitive(True)
            return
        total_seconds = time.time() - self.test_start_time
        total_minutes = int(total_seconds / 60)
        total_hours   = total_minutes / 60
        total_minutes = total_minutes % 60
        total_sec_frac = int(total_seconds * 100) % 100
        total_seconds = int(total_seconds % 60)
        self.run_lab.set_text("%s - %02u:%02u:%02u.%02u" % \
            (self.context.tests_group.name,
             total_hours, total_minutes, total_seconds, total_sec_frac))

    def finished(self):

        self.run_group_man.wait_for_end()

        self.run_ok_btn.set_sensitive(True)
        self.test_list.set_sensitive(True)
        self.dev_list.set_sensitive(True)
        self.progress_bar.set_fraction(1)

        if not len(self.run_group_man.session_results):
            open_notify_gui(self.context, "No Results.\nNo Devices?")

        self.update_status_time()
        self._stop_update()

    def select_testfile(self, select_testfile):
        test_list = self.test_list
        selector = test_list.get_selection()
        test_list_store = test_list.get_model()
        for testfile in test_list_store:
            if testfile[0] == select_testfile:
                selector.select_iter(testfile.iter)
                test_list.scroll_to_cell(
                    test_list_store.get_path(testfile.iter),
                    None, False, 0, 0)
                self.out_buf.set_text("")
                break


    def select_dev(self, select_dev_uuid):
        dev_list = self.dev_list
        selector = dev_list.get_selection()
        dev_list_store = dev_list.get_model()
        for dev_uuid in dev_list_store:
            if dev_uuid[0] == select_dev_uuid:
                selector.select_iter(dev_uuid.iter)
                dev_list.scroll_to_cell(
                    dev_list_store.get_path(dev_uuid.iter),
                    None, False, 0, 0)
                break
        test_list_store = self.test_list.get_model()
        for treeiter in test_list_store:
            treeiter[1] = None

    def start_outfile(self, outfile):
        self.test_time = time.time()
        self.out_text.get_buffer().set_text("")

    def start_logfile(self, logfile):
        self.log_text.get_buffer().set_text("")

    def test_status(self, args):
        passfail = args.split(' ')[0]
        passfail = passfail == "True"
        test_list = self.test_list
        selection = test_list.get_selection()
        test_list_store = test_list.get_model()
        treeiters = selection.get_selected_rows()[1]
        for treeiter in treeiters:
            test_list_store[treeiter][1] = get_pass_fail_icon_name(passfail)
        self.test_time = 0

    def dev_status(self, passfail):
        dev_list = self.dev_list
        selection = dev_list.get_selection()
        dev_list_store = dev_list.get_model()
        treeiters = selection.get_selected_rows()[1]
        for treeiter in treeiters:
            dev_list_store[treeiter][1] = get_pass_fail_icon_name(passfail)

    def dev_set_uuid(self, new_uuid):
        dev_list = self.dev_list
        selection = dev_list.get_selection()
        dev_list_store = dev_list.get_model()
        treeiters = selection.get_selected_rows()[1]
        for treeiter in treeiters:
            dev_list_store[treeiter][0] = new_uuid

    def _stop_update(self):
        if not self.update_id is None:
            GLib.source_remove(self.update_id)
            self.update_id = None

    def go_back(self):
        self._stop_update()
        self.total_duration = None
        self.context.pop_view()


    def on_ok(self):

        self.run_group_man.submit()

        self.go_back()


    def force_stop(self):
        self.run_group_man.stop()
        self._stop_update()


    def on_cancel(self):
        if self.run_group_man.live:
            self.force_stop()
            self.test_list.set_sensitive(True)
            self.dev_list.set_sensitive(True)
            self.run_group_man.readonly = True
        else:
            # If test finished, cancel is same as ok.
            self.on_ok()


    def on_redo(self):
        self.force_stop()
        # Submit results, which will only happen if tests finished.
        self.run_group_man.submit()
        # Clean files would happen in submit, but only if tests finished.
        self.run_group_man.clean_files()
        self.start_test_group()
        self.run_lab.set_text(self.context.tests_group.name)


    def on_info(self):
        self.run_info.set_visible(self.info_btn.get_active())
        btn_r = self.info_btn.get_allocation()
        self.run_split_box.set_position(btn_r.width)
        if self.run_group_man.readonly and self.info_btn.get_active():
            self.load_info()


    def _run(self):
        self.run_ok_btn.set_sensitive(False)
        self.test_list.set_sensitive(False)
        self.dev_list.set_sensitive(False)

        self.out_buf.set_text("")

        context = self.context
        tests_group = context.tests_group

        self.progress_bar.set_fraction(0)
        if tests_group.duration:
            self.total_duration = tests_group.duration * len(context.devices)
        else:
            self.total_duration = None
        if self.update_id is None:
            self.update_id = GLib.timeout_add(250, self.update_progress)

        self.test_time = 0
        self.total_test_time = 0
        self.test_start_time = time.time()
        if not self.run_group_man.start():
            self.finished()


    def start_test_group(self):

        test_list_store = self.test_list.get_model()
        dev_list_store = self.dev_list.get_model()

        test_list_store.clear()
        dev_list_store.clear()

        for test in self.context.tests_group.tests:
            test_list_store.append([test.name, "", test])

        for dev in self.context.devices:
            dev_list_store.append([dev.uuid, ""])

        self._run()


    def _scroll_to_end(self, widget, alloc):
        adj = widget.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def _log_line(self, line, tag):
        self.log_buf.insert_with_tags(self.log_buf.get_end_iter(),
                                      line, tag)

    def _error_line(self, line):
        self._log_line(line, self.err_tag)

    def _warning_line(self, line):
        self._log_line(line, self.warn_tag)

    def _info_line(self, line):
        self._log_line(line, self.info_tag)


    def _out_line(self, line, tag):
        self.out_buf.insert_with_tags(self.out_buf.get_end_iter(), line, tag)

    def _good_line(self, line):
        self._out_line(line[6:], self.good_tag)

    def _bad_line(self, line):
        self._out_line(line[5:], self.bad_tag)

    def _normal_line(self, line):
        self._out_line(line, self.norm_tag)


    def update_progress(self):
        if self.total_duration and self.test_time:
            now = time.time()
            self.total_test_time += now - self.test_time
            self.test_time = now

            fraction = self.total_test_time / self.total_duration

            self.progress_bar.set_fraction(fraction)

        self.update_status_time()

        return True

    def select_dev_list(self):
        if not self.run_group_man.readonly:
            return
        test_list_store = self.test_list.get_model()
        dev_sel = self.dev_list.get_selection()
        dev_model, dev_iters = dev_sel.get_selected_rows()
        if len(dev_iters):
            dev = dev_model[dev_iters[0]][0]
            for test_result in test_list_store:
                test = test_result[0]
                pass_fail = self.run_group_man.is_pass(dev, test)
                if pass_fail < 0:
                    test_result[1] = ""
                else:
                    test_result[1] = get_pass_fail_icon_name(pass_fail)
        else:
            for test_result in test_list_store:
                test_result[1] = ""
        self.load_info()

    def load_info(self):
        if not self.run_group_man.readonly:
            return
        dev_sel = self.dev_list.get_selection()
        test_sel = self.test_list.get_selection()

        dev_model, dev_iters = dev_sel.get_selected_rows()
        test_model, test_iters = test_sel.get_selected_rows()

        self.log_text.get_buffer().set_text("")
        self.out_text.get_buffer().set_text("")

        if not self.run_info.get_visible():
            return

        if len(dev_iters) and len(test_iters):
            dev = dev_model[dev_iters[0]][0]
            test = test_model[test_iters[0]][0]

            self.run_group_man.load_files(dev, test)


    def load_session(self, session):

        self.run_group_man.load_session(session)

        dev_list_store = self.dev_list.get_model()
        dev_list_store.clear()
        for uuid, dev_results in session.devices.items():
            dev_list_store.append([uuid, get_pass_fail_icon_name(dev_results.pass_fail)])

        test_list_store = self.test_list.get_model()
        test_list_store.clear()
        for name in session.tests:
            test_list_store.append([name, "", None])

        selector = self.dev_list.get_selection()
        for dev_uuid in dev_list_store:
            selector.select_iter(dev_uuid.iter)
            break
        self.progress_bar.set_fraction(1)
        self.test_list.set_sensitive(True)
        self.dev_list.set_sensitive(True)

    def set_run_ready(self):
        self.run_group_man.readonly = False



def set_run_context_singleton(_custom_run_context):
    global _run_context
    _run_context = _custom_run_context


def open_run_group(context):

    global _run_context

    _run_context.set_run_ready()

    context.push_view()
    context.change_view("RunGroupViewObj")

    _run_context.run_lab.set_text(context.tests_group.name)


def open_ran_group(context, session):

    global _run_context

    _run_context.load_session(session)

    context.push_view()
    context.change_view("RunGroupViewObj")

    stamp = datetime.datetime.fromtimestamp(session.time_of_tests)

    _run_context.run_lab.set_text('"%s"\n@ %s' % \
                                  (context.tests_group.name, str(stamp)))


def base_init_run_group(context, run_context):

    builder = context.builder

    global _run_context

    _run_context = run_context(context)
