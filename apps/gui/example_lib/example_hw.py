import os
import random
import dt_db_base

from .check_descs import CHECK_DESCS
from dt_db_base import base_hw_dev, base_hw_bus, base_hw_bus_con

## Example device
class example_dev(base_hw_dev):
    def __init__(self, uuid):
        self._uuid = uuid
        self.test_check      = None
        self.threshold_check = None
        self.exact_check     = None
        self.store_value     = None
        self._fw = ""
        self._write_enable = False
        self._hw_id = "%02x:%02x:%02x:%02x:%02x:%02x" % \
                    (random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255))

    def set_test_functions(self, test_check, threshold_check, exact_check, store_value):
        self.threshold_check = threshold_check
        self.exact_check     = exact_check
        self.store_value     = store_value
        self.test_check      = test_check

    def update_uuid_from_hw(self):
        if not self._fw:
            dt_db_base.error_msg("HW ID can not be read without firmware.")
            r = False
        else:
            dt_db_base.info_msg("HW ID: " + self._hw_id)
            self._uuid = self._hw_id
            r = True
        self.exact_check(r, True, CHECK_DESCS.FIRMWARE_HW_ID)

    def read_serial(self):
        r = self._fw
        dt_db_base.info_msg("FW serial: " + r)
        return r

    def read_3v3_rail(self):
        mV = 3299
        dt_db_base.info_msg("Read 3.3 rail as %umV" % mV)
        return mV

    def read_current(self):
        mA = 141
        dt_db_base.info_msg("Current is %umA" % mA)
        return mA

    def read_revision(self):
        return 101

    @property
    def write_enable(self):
        return self._write_enable

    @write_enable.setter
    def write_enable(self, v):
        if self._write_enable == v:
            dt_db_base.warning_msg("Firmware lock already in requested state.")
        self._write_enable = v

    def send_firmware(self, fw):
        if not self._write_enable:
            dt_db_base.error_msg("Firmware locked, but upload attempted.")
            r = False
        else:
            dt_db_base.info_msg("Uploading firmware")
            with open(fw) as f:
                self._fw = f.readline().strip()
            dt_db_base.info_msg("Firmware loaded")
            r = True
        self.exact_check(r, True, CHECK_DESCS.FIRMWARE_PROGRAM)

    def reset(self):
        dt_db_base.info_msg("Device reset")


## Open connection to a Example bus.
class example_bus_con(base_hw_bus_con):
    def __init__(self):
        super().__init__()

    ## Load in known device UUIDs
    def ready_devices(self, known_devices):
        if len(known_devices):
            self._devices = [ example_dev(known_devices[0].uuid) ]
        else:
            self._devices = []

## Example bus ready to be openned for use.
class example_bus(base_hw_bus):
    def __init__(self):
        super().__init__()

    def open(self):
        self._obj = example_bus_con()
        return self._obj
