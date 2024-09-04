class base_hw_dev(object):
    def __init__(self, uuid):
        self._uuid=uuid

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        self._uuid = uuid


class base_hw_bus_con(object):
    def __init__(self):
        self._devices = []

    def ready_devices(self, known_devices):
        raise NotImplementedError

    ## Get the device from the open bus.
    @property
    def devices(self):
        return self._devices

    def poll_devices(self):
        pass


class base_hw_bus(object):
    def __init__(self):
        self._obj = None

    def open(self):
        self._obj = bus_con()
        return self._obj

    def close(self):
        self._obj = None

    def get_current(self):
        return self._obj

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()
