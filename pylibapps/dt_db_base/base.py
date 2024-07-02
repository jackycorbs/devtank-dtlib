import ctypes

from . import int_logging

_logger = int_logging.get_logger(__name__)

try:
    ctypes.cdll.LoadLibrary("libbase.so")
except OSError:
    _logger.debug("USING PYTHON")
    dt_lib_with_c = False
    from .py_base import *
else:
    _logger.debug("USING C")
    dt_lib_with_c = True
    from .c_base import *
