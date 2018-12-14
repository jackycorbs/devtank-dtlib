

## Example device
class example_dev(object):
    def __init__(self):
        self._uuid = "<unknown>"

    ## Get Example device Universal Unique ID
    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid

    ## Example serial number is duplicate of UUID.
    @property
    def serial_number(self):
        return self._uuid



## Open connection to a Example bus.
class example_bus_con(object):
    def __init__(self):
        self._devices = [ example_dev() ]

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
