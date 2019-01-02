from context import gui_context_object

from start_gui import open_start_page, init_start_page
from group_run_gui import init_run_group, open_ran_group, open_run_group
from groups_list_gui import init_groups_list, open_groups_list
from sessions_results_gui import init_tests_sessions_results,     \
                                 open_dev_tests_sessions_results, \
                                 open_tests_sessions_results

from dt_gui_base import init_query_gui,           \
                        init_test_group_selector, \
                        init_tests_properties,    \
                        init_test_group_naming,   \
                        open_test_group_selector, \
                        open_tests_properties,    \
                        open_test_group_naming

def init(context):
    init_start_page(context)
    init_query_gui(context)
    init_run_group(context)
    init_groups_list(context)
    init_test_group_selector(context)
    init_tests_properties(context)
    init_test_group_naming(context)
    init_tests_sessions_results(context)
