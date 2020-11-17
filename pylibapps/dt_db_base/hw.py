from __future__ import print_function, absolute_import

import os
import sys
import time
from ctypes import *

from .c_base import output_normal, output_good, output_bad, c_base_func

_c_libcbase = cdll.LoadLibrary("libhw.so")

def _c_libcbase_func(restype, name, argtypes):
    return c_base_func(_c_libcbase, restype, name, argtypes)


_dt_adj_pwr_get                     = _c_libcbase_func(c_void_p, "dt_adj_pwr_get",                     None)
_dt_adj_pwr_is_setup                = _c_libcbase_func(c_bool,   "dt_adj_pwr_is_setup",                (c_void_p,))
_dt_adj_pwr_load_power_control      = _c_libcbase_func(c_bool,   "dt_adj_pwr_load_power_control",      (c_void_p, c_char_p))
_dt_adj_pwr_shutdown                = _c_libcbase_func(None,     "dt_adj_pwr_shutdown",                (c_void_p,))
_dt_adj_pwr_enable_power_supply     = _c_libcbase_func(c_bool,   "dt_adj_pwr_enable_power_supply",     (c_void_p, c_bool))
_dt_adj_pwr_power_supply_is_enabled = _c_libcbase_func(c_bool,   "dt_adj_pwr_power_supply_is_enabled", (c_void_p,))
_dt_adj_pwr_enable_power_out        = _c_libcbase_func(c_bool,   "dt_adj_pwr_enable_power_out",        (c_void_p, c_bool))
_dt_adj_pwr_power_out_is_enabled    = _c_libcbase_func(c_bool,   "dt_adj_pwr_power_out_is_enabled",    (c_void_p,))
_dt_adj_pwr_set_power_out           = _c_libcbase_func(c_bool,   "dt_adj_pwr_set_power_out",           (c_void_p, c_double))
_dt_adj_pwr_get_power_out           = _c_libcbase_func(c_bool,   "dt_adj_pwr_get_power_out",           (c_void_p, POINTER(c_double)))
_dt_adj_pwr_get_power_use           = _c_libcbase_func(c_bool,   "dt_adj_pwr_get_power_use",           (c_void_p, POINTER(c_double)))

_gpio_obj_create  = _c_libcbase_func(c_void_p, "gpio_obj_create",  None)
_gpio_obj_destroy = _c_libcbase_func(None,     "gpio_obj_destroy", (c_void_p,))
_gpio_obj_read    = _c_libcbase_func(c_bool,   "gpio_obj_read",    (c_void_p, POINTER(c_bool)))
_gpio_obj_write   = _c_libcbase_func(c_bool,   "gpio_obj_write",   (c_void_p, c_bool))


class power_controller_t(object):
    def __init__(self):
        self._c_ptr = _dt_adj_pwr_get()
        self.use_stderr = False

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

    def _do_msg(self, msg_type, msg):
        if self.use_stderr:
            print(msg, file=sys.stderr)
        elif msg_type == "good":
            output_good(msg)
        elif msg_type == "bad":
            output_bad(msg)
        else:
            output_normal(msg)

    def set_voltage_and_wait(self, v, wait_seconds=3):
        self.voltages_out = v
        if not wait_seconds:
            return
        ref = v if v else 1
        # Give supply time to ramp up.
        for n in range(0, wait_seconds):
            v_cur = self.voltages_out
            if abs(v_cur - v) / ref > 0.1:
                self._do_msg(None, "Powering up to %Gv at %Gv" % \
                              (v, v_cur))
                time.sleep(1)
            else:
                self._do_msg("good", "Powered to %Gv" % v_cur)
                return
        self._do_msg("bad", "Failed to power to %Gv in %u seconds given" % \
            (v, wait_seconds))



class gpio_t(object):
    def __init__(self):
        self._c_ptr = None

    def open(self, gpio_number):
        if self._c_ptr:
            _gpio_obj_destroy(self._c_ptr)
        path = "/sys/class/gpio/gpio%u" % gpio_number
        self._c_ptr = _gpio_obj_create(path)
        assert self._c_ptr, "GPIO open failed."

    def close(self):
        if self._c_ptr:
            _gpio_obj_destroy(self._c_ptr)
        self._c_ptr = None

    @property
    def is_open(self):
        return bool(self._c_ptr)

    @property
    def value(self):
        v = c_bool()
        assert _gpio_obj_read(self._c_ptr, byref(v)), "GPIO read failed."
        return v

    @value.setter
    def value(self, v):
        assert _gpio_obj_write(self._c_ptr, v), "GPIO write failed."
