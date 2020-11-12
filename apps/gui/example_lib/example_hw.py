import random

## Example device
class example_dev(object):
    def __init__(self, uuid):
        self._uuid=uuid
        self.test_check      = None
        self.threshold_check = None
        self.exact_check     = None
        self.store_value     = None

    def set_test_functions(self, test_check, threshold_check, exact_check, store_value):
        self.threshold_check = threshold_check
        self.exact_check     = exact_check
        self.store_value     = store_value
        self.test_check      = test_check

    ## Get Example device Universal Unique ID
    @property
    def uuid(self):
        return self._uuid

    def update_uuid_from_hw(self):
        self.test_check(True, "Internal binding check")
        self.uuid = "%02x:%02x:%02x:%02x:%02x:%02x" % \
                    (random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255),
                     random.randint(0, 255))
    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid



## Open connection to a Example bus.
class example_bus_con(object):
    def __init__(self):
        self._devices = []

    ## Load in known device UUIDs
    def ready_devices(self, known_devices):
        if len(known_devices):
            self._devices = [ example_dev(known_devices[0].uuid) ]
        else:
            self._devices = []

    ## Get the Example device from the open bus.
    @property
    def devices(self):
        return self._devices

    ## Poll devices, which on this bus is a null-op.
    def poll_devices(self):
        pass


## Example bus ready to be openned for use.
class example_bus(object):
    def __init__(self):
        self._obj = None

    def open(self):
        self._obj = example_bus_con()
        return self._obj

    def close(self):
        self._obj = None

    def get_current(self):
        return self._obj

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()
