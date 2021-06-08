from __future__ import print_function, absolute_import

import os
import sys
import parser

from .group_selector_gui import open_test_group_selector
from .common import create_list_store
from .sessions_results_gui import open_tests_sessions_results
from .base_group_run_gui import open_run_group
from .notify_gui import open_notify_gui

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk



class base_groups_list_gui(object):
    def __init__(self, context):
        self.context = context

        from .group_properties_gui import create_list_store

        builder = context.builder

        self.group_info = builder.get_object("group_desc_text")
        self.groups_list = context.builder.get_object("GroupActList")

        self.groups_store = create_list_store(self.groups_list, False, 0.8)

        self.back_btn = builder.get_object("group_act_back_btn")
        self.run_btn = builder.get_object("group_run_btn")
        self.new_btn = builder.get_object("group_new_btn")
        self.copy_btn = builder.get_object("group_clone_btn")
        self.edit_btn = builder.get_object("group_edit_btn")
        self.delete_btn = builder.get_object("group_delete_btn")
        self.results_btn = builder.get_object("group_results_btn")
        self.adv_more_btn = builder.get_object("adv_more_btn")

        self.back_btn.connect("clicked", lambda btn: self._on_back_btn())
        self.run_btn.connect("clicked", lambda btn: self._on_run_btn())
        self.new_btn.connect("clicked", lambda btn: self._on_new_btn())
        self.copy_btn.connect("clicked", lambda btn: self._on_copy_btn())
        self.edit_btn.connect("clicked", lambda btn: self._on_edit_btn())
        self.delete_btn.connect("clicked", lambda btn: self._on_delete_btn())
        self.results_btn.connect("clicked", lambda btn: self._results_btn())
        self.adv_more_btn.connect("clicked", lambda btn: self._more_btn())

        self.btns = [self.run_btn, self.results_btn, self.copy_btn,
                     self.edit_btn, self.delete_btn]

        selection = self.groups_list.get_selection()
        selection.connect("changed", lambda sel : self._on_list_selection_changed())

        context.view_objs["TestGroupActSelectorObj"] = self


    def _use_selection(self):
        list_obj = self.groups_list

        list_store = list_obj.get_model()
        selection = list_obj.get_selection()
        treeiters = selection.get_selected_rows()[1]

        tests_group = self.context.tests_group

        for treeiter in treeiters:
            tests_group.populate_from(list_store[treeiter[0]][1])


    def _on_back_btn(self):
        self.context.pop_view()

    def _on_new_btn(self):

        tests_group = self.context.tests_group

        tests_group.clear()

        open_test_group_selector(self.context)

    def _on_copy_btn(self):
        self._use_selection()
        self.context.tests_group.db_group = None
        open_test_group_selector(self.context)

    def _on_edit_btn(self):
        self._use_selection()
        open_test_group_selector(self.context)


    def _on_delete_btn(self):
        list_obj = self.groups_list

        list_store = list_obj.get_model()
        selection = list_obj.get_selection()
        treeiters = selection.get_selected_rows()[1]

        for treeiter in treeiters:
            db_group = list_store[treeiter[0]][1]
            db_group.delete()
            list_store.remove(list_store.get_iter(treeiter))


    def _on_run_btn(self):
        if len(self.context.devices):
            self._use_selection()
            open_run_group(self.context)
        else:
            open_notify_gui(self.context, "No devices known.")

    def _results_btn(self):
        self._use_selection()
        open_tests_sessions_results(self.context)

    def _more_btn(self):
        self._use_selection()
        # Override


    def show_view(self):
        builder = self.context.builder

        self.context.force_view("TestGroupActSelector")

        is_advanced = not bool(self.context.args["production"])

        for advanced_only in ["group_new_btn",
                              "group_clone_btn",
                              "group_edit_btn",
                              "group_delete_btn",
                              "adv_more_btn"]:
            btn = builder.get_object(advanced_only)
            btn.set_visible(is_advanced)

        if not self.context.db:
            self.context.db_init()
            if not self.context.db:
                self._on_back_btn()
                return

        groups = self.context.db.get_groups()

        groups_store = self.groups_list.get_model()

        groups_store.clear()
        for group in groups:
            if is_advanced or \
               not hasattr(group,"is_commission_group") or \
               not group.is_commission_group():
                groups_store.append([group.name, group])

        for btn in self.btns:
            btn.set_sensitive(False)


    def _on_list_selection_changed(self):

        selection = self.groups_list.get_selection()

        model, treeiters = selection.get_selected_rows()
        self.group_info.get_buffer().set_text("")

        enabled = False

        for treeiter in treeiters:
            group = model[treeiter][1]
            self.group_info.get_buffer().set_text(group.desc)
            enabled = True

        for btn in self.btns:
            btn.set_sensitive(enabled)
