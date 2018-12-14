import os
import time
import c_base

from dt_db_base import base_run_group_context, base_run_group_manager



class _run_group_context(base_run_group_context):
    lib_inf = c_base

    def __init__(self, context, bus, last_end_time, stdout_out):
        tmp_dir="/tmp"
        base_run_group_context.__init__(self, context, bus, last_end_time, stdout_out, tmp_dir)
        self.db_dev = context.db_dev

    def get_ready_devices(self, bus_con, prep_device=True):
        r = bus_con.devices
        if len(r):
            dev = r[0]
            dev.uuid = self.db_dev.uuid
            dev.supply_enabled = True
        return r

    def stop_devices(self):
        bus_con = self.bus.get_current()
        if bus_con:
            if len(bus_con.devices):
                bus_con.devices[0].supply_enabled = False
        else:
            with self.bus as bus_con:
                if len(bus_con.devices):
                    bus_con.devices[0].supply_enabled = False

    def finished(self, bus_con):
        base_run_group_context.finished(self, bus_con)
        if len(bus_con.devices):
            bus_con.devices[0].supply_enabled = False


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
