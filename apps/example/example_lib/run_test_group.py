import os
import time

from dt_db_base import base_run_group_context, \
                       base_run_group_manager, \
                       c_base



class _run_group_context(base_run_group_context):
    lib_inf = c_base

    def __init__(self, context, bus, last_end_time, stdout_out):
        tmp_dir="/tmp"
        base_run_group_context.__init__(self, context, bus, last_end_time, stdout_out, tmp_dir)
        self.devices = context.devices

    def get_ready_devices(self, bus_con):
        bus_con.ready_devices(self.devices)
        return bus_con.devices

    def stop_devices(self):
        pass


class run_group_manager(base_run_group_manager):
        def __init__(self, context,
                 good_line = None,
                 bad_line = None,
                 normal_line = None,
                 info_line = None,
                 warning_line = None,
                 error_line = None,
                 cmds = None):
            base_run_group_manager.__init__(self,
                                            context,
                                            _run_group_context,
                                            good_line,
                                            bad_line,
                                            normal_line,
                                            info_line,
                                            warning_line,
                                            error_line,
                                            cmds)
