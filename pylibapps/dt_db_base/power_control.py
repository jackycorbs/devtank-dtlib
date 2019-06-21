from __future__ import print_function

import os
import time
from ctypes import *

from c_base import output_normal, output_good, output_bad

_c_libcbase = cdll.LoadLibrary("libhw.so")

def c_libcbase_func(restype, name, argtypes):
    """Export C function from shared C library."""
    r = getattr(_c_libcbase, name)
    r.restype = restype
    r.argtypes = argtypes
    return r


_dt_adj_pwr_get                     = c_libcbase_func(c_void_p, "dt_adj_pwr_get",                     None)
_dt_adj_pwr_is_setup                = c_libcbase_func(c_bool,   "dt_adj_pwr_is_setup",                (c_void_p,))
_dt_adj_pwr_load_power_control      = c_libcbase_func(c_bool,   "dt_adj_pwr_load_power_control",      (c_void_p, c_char_p))
_dt_adj_pwr_shutdown                = c_libcbase_func(None,     "dt_adj_pwr_shutdown",                (c_void_p,))
_dt_adj_pwr_enable_power_supply     = c_libcbase_func(c_bool,   "dt_adj_pwr_enable_power_supply",     (c_void_p, c_bool))
_dt_adj_pwr_power_supply_is_enabled = c_libcbase_func(c_bool,   "dt_adj_pwr_power_supply_is_enabled", (c_void_p,))
_dt_adj_pwr_enable_power_out        = c_libcbase_func(c_bool,   "dt_adj_pwr_enable_power_out",        (c_void_p, c_bool))
_dt_adj_pwr_power_out_is_enabled    = c_libcbase_func(c_bool,   "dt_adj_pwr_power_out_is_enabled",    (c_void_p,))
_dt_adj_pwr_set_power_out           = c_libcbase_func(c_bool,   "dt_adj_pwr_set_power_out",           (c_void_p, c_double))
_dt_adj_pwr_get_power_out           = c_libcbase_func(c_bool,   "dt_adj_pwr_get_power_out",           (c_void_p, POINTER(c_double)))
_dt_adj_pwr_get_power_use           = c_libcbase_func(c_bool,   "dt_adj_pwr_get_power_use",           (c_void_p, POINTER(c_double)))


class power_controller_t(object):
    def __init__(self):
        self._c_ptr = _dt_adj_pwr_get()

    @property
    def is_setup(self):
        return _dt_adj_pwr_is_setup(self._c_ptr)

    def load(self, filename):
        return _dt_adj_pwr_load_power_control(self._c_ptr, filename)

    def shutdown(self):
        _dt_adj_pwr_shutdown(self._c_ptr)

    @property
    def power_supply_enabled(self):
        return _dt_adj_pwr_power_supply_is_enabled(self._c_ptr)

    @power_supply_enabled.setter
    def power_supply_enabled(self, enable):
        return _dt_adj_pwr_enable_power_supply(self._c_ptr, enable)

    @property
    def power_out_enabled(self):
        return _dt_adj_pwr_power_out_is_enabled(self._c_ptr)

    @power_out_enabled.setter
    def power_out_enabled(self, enable):
        return _dt_adj_pwr_enable_power_out(self._c_ptr, enable)

    @property
    def voltages_out(self):
        v = c_double()
        if not _dt_adj_pwr_get_power_out(self._c_ptr, byref(v)):
            raise Exception("Failed to get power out value.")
        return v.value

    @voltages_out.setter
    def voltages_out(self, voltage):
        if not  _dt_adj_pwr_set_power_out(self._c_ptr, voltage):
            raise Exception("Failed to set power out value.")

    @property
    def current(self):
        v = c_double()
        if not _dt_adj_pwr_get_power_use(self._c_ptr, byref(v)):
            raise Exception("Failed to get power use value.")
        return v.value

    def set_voltage_and_wait(self, v, wait_seconds=3):
        self.voltages_out = v
        if not wait_seconds:
            return
        ref = v if v else 1
        # Give supply time to ramp up.
        for n in range(0, wait_seconds):
            v_cur = self.voltages_out
            if abs(v_cur - v) / ref > 0.1:
                output_normal("Powering up to %Gv at %Gv" % \
                              (v, v_cur))
                time.sleep(1)
            else:
                output_good("Powered to %Gv" % v_cur)
                return
        output_bad("Failed to power to %Gv in %u seconds given" % \
            (v, wait_seconds))

