from __future__ import print_function, absolute_import

import sys
from dt_gui_base import base_groups_list_gui, open_notify_gui

_singleton = None

from .group_run_gui import open_run_group
from .sessions_results_gui import open_tests_sessions_results


class groups_lists_gui(base_groups_list_gui):
    def __init__(self, context):
        base_groups_list_gui.__init__(self, context)

    def show_view(self):
        base_groups_list_gui.show_view(self)
        self.adv_more_btn.hide()

    def _on_run_btn(self):
        if len(self.context.devices):
            self._use_selection()
            open_run_group(self.context)
        else:
            open_notify_gui(self.context, "No devices known.")

    def _results_btn(self):
        self._use_selection()
        open_tests_sessions_results(self.context)


def open_groups_list(context):
    context.push_view()
    context.change_view("TestGroupActSelectorObj")


def init_groups_list(context):
    _singleton = groups_lists_gui(context)
