from __future__ import print_function, absolute_import

import sys

from .context import gui_context_object

from .start_gui import open_start_page, init_start_page
from .group_run_gui import init_run_group, open_ran_group, open_run_group
from .groups_list_gui import init_groups_list, open_groups_list


from dt_gui_base import dt_gui_base_init, \
                        open_test_group_selector, \
                        open_tests_properties,    \
                        open_test_group_naming,   \
                        open_dev_tests_sessions_results, \
                        open_tests_sessions_results

def init(context):
    dt_gui_base_init(context)
    init_start_page(context)
    init_run_group(context)
    init_groups_list(context)
