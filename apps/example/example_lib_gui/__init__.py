from context import gui_context_object

from start_gui import open_start_page, init_start_page

from dt_gui_base import base_groups_list_gui, init_query_gui

_groups_singleton = None


def open_groups_list(context):
    context.push_view()
    context.change_view("TestGroupActSelectorObj")


def init(context):
    global _groups_singleton
    init_start_page(context)
    _groups_singleton = base_groups_list_gui(context)

    init_query_gui(context)
