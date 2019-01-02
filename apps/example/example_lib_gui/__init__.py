from context import gui_context_object

from start_gui import open_start_page, init_start_page
from group_run_gui import init_run_group, open_ran_group, open_run_group
from groups_list_gui import init_groups_list, open_groups_list

from dt_gui_base import init_query_gui


def init(context):
    init_start_page(context)
    init_query_gui(context)
    init_run_group(context)
    init_groups_list(context)
