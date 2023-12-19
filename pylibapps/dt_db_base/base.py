import ctypes

try:
    ctypes.cdll.LoadLibrary("libbase.so")
except OSError:
    print("USING PYTHON")
    from .py_base import *
else:
    print("USING C")
    from .c_base import *
