import sys
from dt_gui_base import base_groups_list_gui

_singleton = None


class groups_lists_gui(base_groups_list_gui):
    def __init__(self, context):
        base_groups_list_gui.__init__(self, context)

    def show_view(self):
        base_groups_list_gui.show_view(self)
        self.adv_more_btn.hide()


def open_groups_list(context):
    context.push_view()
    context.change_view("TestGroupActSelectorObj")


def init_groups_list(context):
    _singleton = groups_lists_gui(context)
