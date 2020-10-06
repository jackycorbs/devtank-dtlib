import os
import sys

import example_lib
import example_lib_gui

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib

from dt_gui_base import scan_box_base, open_query_gui


_singleton = None


class fake_example_dev(object):
    def __init__(self, serial_number, uuid):
        self.serial_number = serial_number
        self.uuid          = uuid


def _board_in_rig(context, db_dev, next_view, serial_number, yes_no):

    if not yes_no:
        return

    if not db_dev:
        db_dev = example_lib.db_example_dev.create(context.db, serial_number, "UNSET")
        db_dev.update_uuid("<unknown>-%u" % db_dev.id)
    context.devices = [fake_example_dev(serial_number, db_dev.uuid)]

    next_view(context)


def _is_board_in_rig(context, db_dev, next_view, serial_number):
    open_query_gui("Place board in test fixture.\nIs it now in the fixture?",
                           lambda yes_no: _board_in_rig(context, db_dev, next_view, serial_number, yes_no))


def _view_results(context, db_dev, next_view, serial_number, yes_no):

    if yes_no:
        from .sessions_results_gui import open_dev_tests_sessions_results
        context.devices = [fake_example_dev(serial_number, db_dev.uuid)]
        open_dev_tests_sessions_results(context, db_dev)
        return

    _is_board_in_rig(context, db_dev, next_view, serial_number)


class _start_double_scan(scan_box_base):
    def __init__(self, context):
        scan_box_base.__init__(self, context,
                               "start_scan_barcodeA_entry",
                               "start_scan_barcodeB_entry")
        self.start_scan_status_lab = context.builder.get_object("start_scan_status_lab")

    def reset_scan(self):
        scan_box_base.reset_scan(self)

    def barcode_do(self, serial_number):
        context = self.context

        if not context.db:
            if not context.db_init():
                self.set_status("Unable to connect to DB.")
                return

        if context.args['production']:
            db_test_group = context.db.get_group("Example Group")
            context.tests_group.populate_from(db_test_group)
            from .group_run_gui import open_run_group
            next_view = open_run_group
        else:
            next_view = example_lib_gui.open_groups_list

        db_dev = example_lib.db_example_dev.get_by_serial(context.db, serial_number)
        if not db_dev:
            _is_board_in_rig(context, db_dev, next_view, serial_number)
        else:
            open_query_gui("Board known, view results?",
                           lambda yes_no: _view_results(context, db_dev, next_view, serial_number, yes_no))

    def set_status(self, msg):
        self.start_scan_status_lab.set_text(msg)


def _poweroff(yes_no):
    if yes_no:
        os.system("systemctl poweroff")



class _start_singleton(object):
    def __init__(self, context):
        self.context = context
        builder = context.builder
        self.scan_view = _start_double_scan(context)
        self.quit_btn = builder.get_object("start_quit_btn")
        self.scan_view.open()

        self.quit_btn.connect("clicked", lambda x: self._clicked_quit())

        context.view_objs["StartViewObj"] = self

        self.refresh_id = GLib.timeout_add_seconds(5,
                                               lambda : self._refresh())

    def _refresh(self):
        if self.context.db_error:
            self.scan_view.set_status("Bad Database connection")
            if self.context.db_init():
                self.scan_view.set_status("Database connected")
                self.scan_view.set_enable(True)
            else:
                self.scan_view.set_enable(False)

        if self.context.db:
            self.context.db.clean()

        return True

    def show_view(self):

        self.context.force_view("Start")

        if self.context.args['production']:
            self.quit_btn.set_label("Shutdown")
        else:
            self.quit_btn.set_label("Quit")

        self.scan_view.reset_scan()
        self._refresh()


    def _clicked_quit(self):
        if self.context.args['production']:
            open_query_gui("Clicked Power Off\nAre you sure?",
                           lambda yes_no: _poweroff(yes_no))
        else:
            self.context.close_app()


def open_start_page(context):
    context.change_view("StartViewObj")

def init_start_page(context):
    global _singleton
    _singleton = _start_singleton(context)
