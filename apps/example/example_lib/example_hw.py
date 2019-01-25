import random

## Example device
class example_dev(object):
    def __init__(self, uuid="<unknown>"):
        self._uuid=uuid

    ## Get Example device Universal Unique ID
    @property
    def uuid(self):
        return self._uuid

    def update_uuid_from_hw(self):
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
