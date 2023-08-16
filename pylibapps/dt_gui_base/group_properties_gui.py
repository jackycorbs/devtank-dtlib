from __future__ import print_function, absolute_import

import os
import sys
import copy

from .query_gui import open_query_gui
from .notify_gui import open_notify_gui
from .group_naming_gui import open_test_group_naming
from .barcode_scan_gui import scan_box_base
from .common import get_float_prop_digits, create_list_store

from dt_db_base import get_test_doc, get_args_in_src, db_is_str_class, dbfile

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk


_singleton = None



class _prop_scan(scan_box_base):
    def __init__(self, parent, test, arg, scan_grid, box_a, box_b):
        scan_box_base.__init__(self, context, box_a, box_b)
        self.parent = parent
        self.test = test
        self.arg = arg
        self.scan_grid = scan_grid

    def open(self):
        self.scan_grid.set_sensitive(True)
        scan_box_base.open(self)

    def barcode_do(self, serial_number):
        self.test.pending_properties[self.arg] = serial_number
        self.close()
        self.scan_barcodeA_entry.set_text(serial_number)
        self.scan_barcodeB_entry.set_text(serial_number)
        self.scan_grid.set_sensitive(False)
        n = self.parent._scans.index(self)
        if n + 1 < len(self.parent._scans):
            self.parent._scans[n + 1].open()
        else:
            unsets = self.parent.context.tests_group.get_unset()
            if not unsets:
                self.parent._clicked_ok()



class group_properties_singleton(object):
    def __init__(self, context):
        self.context = context
        self._next_view_cb = None
        self._support_unset = True
        self._only_unset = False
        self._scans = []
        builder = context.builder

        window = builder.get_object("TestGroupProperties")

        tests_list = builder.get_object("TestsList")
        test_desc = builder.get_object("TestText")
        back_btn = builder.get_object("prop_back_btn")
        ok_btn = builder.get_object("prop_ok_btn")
        test_paras = builder.get_object("TestParas")

        tests_store = create_list_store(tests_list)

        selection = tests_list.get_selection()
        selection.connect("changed", lambda sel : self._on_list_selection_changed(test_desc,
                                                                                  test_paras,
                                                                                  context.tests_group,
                                                                                  sel))
        back_btn.connect("clicked", lambda btn: self._clicked_back())
        ok_btn.connect("clicked", lambda btn: self._clicked_ok())


    def _value_change(self, test, arg, lab, value):
        tests_group = self.context.tests_group
        val_type = tests_group.props_defaults[arg]['type']
        if val_type is not dbfile:
            value = val_type(value)
        elif val_type is dbfile:
            assert value[0] is dbfile
            widgets = value[3]
            value = value[0:3]
            if value[1] is None:
                if value[2] is None:
                    return
                value = (dbfile,
                         tests_group.db.get_file_to_local(value[2]),
                         value[2])
                widgets[1].unselect_all()
            else:
                if not len(value[1]):
                    return
                widgets[0].set_active(-1)

        lab.modify_fg(Gtk.StateFlags.NORMAL, None)
        test.pending_properties[arg] = value


    def _adjuster_from_entry(self, entry, places):
        t = lambda v: float(v) if places else int(v)
        return Gtk.Adjustment(value=t(entry['value']),
                              lower=t(entry['min']),
                              upper=t(entry['max']),
                              step_increment=t(entry['step']))


    def _add_arg(self, tests_group, test, arg, grid, all_files):
        context = self.context
        assert arg in tests_group.props_defaults
        entry = copy.copy(tests_group.props_defaults[arg])
        val_type = entry['type']
        test_props_values = test.pending_properties
        val_value = test_props_values[arg] if arg in test_props_values else None
        lab = Gtk.Label(arg)
        if val_value is None:
            lab.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("red"))
            val_value = entry['default'] if 'default' in entry else None
        entry['value'] = val_value
        grid.add(lab)
        if db_is_str_class(val_type):
            if self._only_unset:
                scan_grid = Gtk.Grid(column_spacing=10,row_spacing=10)
                scan_grid.attach(Gtk.Label("scan 1"), 0, 0, 1, 1)
                scan_grid.attach(Gtk.Label("scan 2"), 0, 1, 1, 1)
                scan_a = Gtk.Entry()
                scan_b = Gtk.Entry()
                scan_grid.attach(scan_a, 1, 0, 1, 1)
                scan_grid.attach(scan_b, 1, 1, 1, 1)
                grid.attach_next_to(scan_grid, lab, Gtk.PositionType.RIGHT, 1, 1)
                scan_grid.set_sensitive(False)
                scan_box = _prop_scan(self, test, arg, scan_grid, scan_a, scan_b)
                self._scans += [ scan_box ]
            else:
                entrybox = Gtk.Entry()
                if val_value is not None:
                    entrybox.set_text(str(val_value))
                entrybox.connect("changed", lambda x: self._value_change(test, arg, lab, x.get_text()))
                grid.attach_next_to(entrybox, lab, Gtk.PositionType.RIGHT, 1, 1)
        elif val_type is int:
            adjustment = self._adjuster_from_entry(entry, 0)
            spin = Gtk.SpinButton(adjustment=adjustment)
            spin.connect("value-changed", lambda x: self._value_change(test, arg, lab, x.get_value_as_int()))
            grid.attach_next_to(spin, lab, Gtk.PositionType.RIGHT, 1, 1)
        elif val_type is float:
            places = get_float_prop_digits(entry)
            adjustment = self._adjuster_from_entry(entry, places)
            spin = Gtk.SpinButton(adjustment=adjustment)
            spin.connect("value-changed", lambda x: self._value_change(test, arg, lab, x.get_value()))
            spin.set_digits(places)
            grid.attach_next_to(spin, lab, Gtk.PositionType.RIGHT, 1, 1)
        elif val_type is bool:
            btn = Gtk.CheckButton()
            if val_value is not None:
                btn.set_active(bool(val_value))
            btn.connect("toggled", lambda x: self._value_change(test, arg, lab, x.get_active()))
            grid.attach_next_to(btn, lab, Gtk.PositionType.RIGHT, 1, 1)
        elif val_type is dbfile:
            files_store = Gtk.ListStore(str, int)
            files_drop = Gtk.ComboBox()
            files_drop.set_model(files_store)
            cell = Gtk.CellRendererText()
            files_drop.pack_start(cell, True)
            files_drop.add_attribute(cell, "text", 0)
            all_file_ids = list(all_files.keys())
            for file_id in all_file_ids:
                filename = all_files[file_id]
                files_store.append(["%i:%s" % (file_id, filename), file_id])
            grid.attach_next_to(files_drop, lab, Gtk.PositionType.RIGHT, 1, 1)
            if val_value is not None and val_value[2] is not None:
                files_drop.set_active(all_file_ids.index(val_value[2]))
            btn = Gtk.FileChooserButton()
            if val_value is not None and val_value[2] is None:
                btn.set_filename(val_value[1])
            grid.attach_next_to(btn, files_drop, Gtk.PositionType.RIGHT, 1, 1)

            files_drop.connect("changed", lambda x: self._value_change(
                test, arg, lab,
                (dbfile, None,
                 files_store[files_drop.get_active()][1] \
                    if files_drop.get_active() >= 0 else None,
                 (files_drop, btn))))

            btn.connect("file-set", lambda x: self._value_change(
                test, arg, lab,
                (dbfile, x.get_filename(), None, (files_drop, btn))))
        else:
            raise Exception("Unknown property type : %s" % str(val_type))


    def _on_list_selection_changed(self, text_obj, test_paras, tests_group, selection):
        context = self.context
        builder = context.builder
        all_files = context.db.get_resource_files()
        model, treeiters = selection.get_selected_rows()
        text_obj.get_buffer().set_text("")
        test_props = builder.get_object("TestProps")
        old_props = test_props.get_children()
        for child in old_props:
            test_props.remove(child)

        self._scans = []

        for treeiter in treeiters:
            test = model[treeiter][1]
            test_file = test.get_file_to_local()
            doc_text = get_test_doc(test_file)
            args = get_args_in_src(test_file)
            text_obj.get_buffer().set_text(doc_text)

            grid = Gtk.Grid(orientation=Gtk.Orientation.VERTICAL)
            grid.set_border_width(10)
            grid.set_row_spacing(10)
            grid.set_column_spacing(10)
            test_props.add(grid)

            for arg in args:
                if self._only_unset:
                    test_props_values = test.pending_properties
                    val_value = test_props_values[arg] if arg in test_props_values else None
                    if val_value is not None:
                        continue
                self._add_arg(tests_group, model[treeiter][1], arg, grid, all_files)

            if len(self._scans):
                self._scans[0].open()

            test_props.show_all()
            break

    def _clicked_back(self):
        if self._next_view_cb:
            self.context.pop_view()
        else:
            self.context.change_view("TestGroupSelector")


    def _select_unset(self, unsets):

        unset, prop = unsets[0]

        tests_list = self.context.builder.get_object("TestsList")
        model = tests_list.get_model()
        for test in model:
            if unset == test[1]:
                sels = tests_list.get_selection()
                sels.unselect_all()
                sels.select_iter(test.iter)
                break


    def _go_to_next_view(self):
        self._scans = []
        if self._next_view_cb:
            self.context.pop_view()
            self._next_view_cb(context)
        else:
            open_test_group_naming(self.context)


    def _leave_unset(self, yes_no, unsets):
        if yes_no:
            self._go_to_next_view()
            return
        self._scans = []
        self._select_unset(unsets)


    def _clicked_ok(self):
        tests_group = self.context.tests_group
        unsets = tests_group.get_unset()
        if unsets:
            window = self.context.builder.get_object("main_window")
            msg = "Unset Properties:\n"

            for test, props in unsets:
                msg += '"%s" has unset:\n' % test.name
                for prop in props:
                    msg += '\t"%s"\n' % prop

            if self._support_unset:
                msg += "Leave unset?"
                open_query_gui(msg,
                               lambda yes_no: \
                                   self._leave_unset(yes_no, unsets))
            else:
                open_notify_gui(context, msg)
                self._leave_unset(False, unsets)

            return

        self._go_to_next_view()


    def open(self, next_view_cb=None, allow_unset=True, only_unset=False):
        context = self.context
        self._next_view_cb = next_view_cb
        self._support_unset = allow_unset
        self._only_unset = only_unset
        if next_view_cb:
            context.push_view()
        context.change_view("TestGroupProperties")
        tests_list = context.builder.get_object("TestsList")
        test_text = context.builder.get_object("TestText")
        tests_list.get_parent().show()
        test_text.get_parent().show()
        tests_store = tests_list.get_model()
        tests_store.clear()
        for test in context.tests_group.tests:
            if not len(test.pending_properties):
                args = get_args_in_src(test.get_file_to_local())
                r = {}
                for arg in args:
                    entry = context.tests_group.props_defaults[arg]
                    r[arg] = entry['default'] if 'default' in entry else entry['min'] if 'min' in entry else None
                test.pending_properties = r
            tests_store.append([test.name, test])

        test_group_test_prop_lab = context.builder.get_object("test_group_test_prop_lab")
        if test_group_test_prop_lab:
            if self._only_unset:
                test_group_test_prop_lab.set_text("Dynamically set properties")
            else:
                test_group_test_prop_lab.set_text("Properties")

        unsets = context.tests_group.get_unset()
        if unsets:
            self._select_unset(unsets)
            if only_unset:
                unset_tests = {}
                for test, props in unsets:
                    unset_tests[test.name] = True
                if len(unset_tests) == 1:
                    tests_list.get_parent().hide()
                    test_text.get_parent().hide()


def open_tests_properties(context, next_view_cb=None, allow_unset=True, only_unset=False):
    _singleton.open(next_view_cb, allow_unset, only_unset)


def init_tests_properties(context):
    global _singleton
    _singleton = group_properties_singleton(context)
