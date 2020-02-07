from barcode_scan_gui import double_scan_view, scan_box_base
from base_group_run_gui import base_run_context, base_init_run_group, open_run_group, open_ran_group, set_run_context_singleton
from common import populate_test_properties, get_pass_fail_icon_name, update_default
from context import gui_context_object
from find_or_create_gui import scan_find_or_create
from new_gui import new_obj_view
from notify_gui import open_notify_gui
from query_gui import open_query_gui

from group_naming_gui import open_test_group_naming

from edit_test_gui import open_edit_test_page
from new_test_gui import open_new_test_page

from sessions_results_gui import base_session_results_singlton

from group_selector_gui import open_test_group_selector
from group_properties_gui import open_tests_properties

from sessions_results_gui import base_session_results_singlton
from groups_list_gui import base_groups_list_gui


def dt_gui_base_init(context):
    from notify_gui import init_notify_gui
    from query_gui import init_query_gui
    from group_selector_gui import init_test_group_selector
    from group_properties_gui import init_tests_properties
    from edit_test_gui import init_edit_test_page
    from new_test_gui import init_new_test_page
    from group_naming_gui import init_test_group_naming
    init_notify_gui(context)
    init_query_gui(context)
    init_test_group_selector(context)
    init_tests_properties(context)
    init_edit_test_page(context)
    init_new_test_page(context)
    init_test_group_naming(context)
