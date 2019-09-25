import datetime

from dt_db_base import default_run_group_manager
from dt_gui_base import base_run_context,   \
                        base_init_run_group,\
                        open_ran_group,     \
                        open_run_group


class _RunContext(base_run_context):
    def __init__(self, context):
        base_run_context.__init__(self, context, default_run_group_manager)

def init_run_group(context):
    base_init_run_group(context, _RunContext)
