from ctypes import cdll, c_int, Structure, c_long, POINTER, byref
import os

clib = cdll.LoadLibrary("libc.so.6")

CLOCK_MONOTONIC = 1
TFD_CLOEXEC = 0o02000000

timerfd_create = getattr(clib, "timerfd_create")
timerfd_create.restype = c_int
timerfd_create.argtypes = (c_int, c_int)

time_t = c_long

class timespec(Structure):
    _fields_ = [("tv_sec", time_t), ("tv_nsec", c_long)]

class itimerspec(Structure):
    _fields_ = [("it_interval", timespec), ("it_value", timespec)]


timerfd_settime = getattr(clib, "timerfd_settime")
timerfd_settime.restype = c_int
timerfd_settime.argtypes = (c_int, c_int, POINTER(itimerspec), POINTER(itimerspec))


def create_timerfd_of(seconds, nanoseconds=0):
    fd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC)
    assert fd > 0, "Failed to create timer fd"
    t = itimerspec()
    t.it_value.tv_sec = seconds
    t.it_value.tv_nsec = nanoseconds
    t.it_interval = t.it_value
    e = timerfd_settime(fd, 0, byref(t), None)
    assert e == 0, "Failed to set timer fd"
    return fd


def drain_timerfd(timer_fd):
    os.read(timer_fd, 8) # Drain timer FD
