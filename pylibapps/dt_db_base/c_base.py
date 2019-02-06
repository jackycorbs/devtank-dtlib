from __future__ import print_function

import os
from ctypes import *
import sys
import atexit

_c_libcbase = cdll.LoadLibrary("libbase.so")

def c_libcbase_func(restype, name, argtypes):
    """Export C function from shared C library."""
    r = getattr(_c_libcbase, name)
    r.restype = restype
    r.argtypes = argtypes
    return r

_ANSI_RED     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_DEFAULT = "\x1B[39m"


# Public imports

## Enable info messages to log.
enable_info_msgs     = c_libcbase_func(None,   "enable_info_msgs",     (c_bool,))
## Enable warning messages to log.
enable_warning_msgs  = c_libcbase_func(None,   "enable_warning_msgs",  (c_bool,))
## Is info messages going to log.
info_msgs_is_enabled = c_libcbase_func(c_bool, "info_msgs_is_enabled", None)
## Get the build information of C library.
## @param build_time Time/Data the C library was built.
## @param git_commit string of the git SHA1 when built.
dt_get_build_info    = c_libcbase_func(None,   "dt_get_build_info",    (POINTER(c_char_p), POINTER(c_char_p)))

## Type used to hand C functions microseconds.
dt_usecs = c_int64

## Convert C microseconds into seconds with fractions.
dt_usecs_to_secs = lambda x : x / 1000000.0

## Convert seconds with fractions into C microseconds.
secs_to_dt_usecs = lambda x : dt_usecs(int(x * 1000000))

# Private imports

_devtank_init     = c_libcbase_func(None, "devtank_init",     None)
_devtank_ready    = c_libcbase_func(c_bool,"devtank_ready",   None)
_devtank_shutdown = c_libcbase_func(None, "devtank_shutdown", None)
_error_msg        = c_libcbase_func(None, "error_msg",        (c_char_p,))
_warning_msg      = c_libcbase_func(None, "warning_msg",      (c_char_p,))
_info_msg         = c_libcbase_func(None, "info_msg",         (c_char_p,))
_set_log_fd       = c_libcbase_func(None, "set_log_fd",       (c_int,))

# Public exports

## Microseconds in a second
USEC_SECOND = 1000000
## Microseconds in a minute.
USEC_MINUTE = (USEC_SECOND * 60)

error_msg   = lambda msg : _error_msg(msg.replace('%','%%'))
warning_msg = lambda msg : _warning_msg(msg.replace('%','%%'))
info_msg    = lambda msg : _info_msg(msg.replace('%','%%'))



def output_bad(msg):
    """ Output information about a fail case. """
    global _msg_stream
    if _msg_stream.isatty():
        print(_ANSI_RED + msg + _ANSI_DEFAULT, file=_msg_stream)
    else:
        print("BAD: %s" % msg, file=_msg_stream)
    _msg_stream.flush()
    lines = msg.splitlines()
    warning_msg("Python bad output: " + lines[0] if len(lines) else "")

def output_good(msg):
    """ Output information about a success case. """
    global _msg_stream
    if _msg_stream.isatty():
        print(_ANSI_GREEN + msg + _ANSI_DEFAULT, file=_msg_stream)
    else:
        print("Good: %s" % msg, file=_msg_stream)
    _msg_stream.flush()
    lines = msg.splitlines()
    info_msg("Python good output: " + lines[0] if len(lines) else "")

def output_normal(msg):
    global _msg_stream
    print(msg, file=_msg_stream)
    _msg_stream.flush()
    lines = msg.splitlines()
    info_msg("Python normal output: " + lines[0] if len(lines) else "")

def set_output(sink):
    if sink:
        assert isinstance(sink, file)
        global _msg_stream
        _msg_stream = sink
    else:
        _msg_stream = sys.stdout


def make_c_buffer_from(buf, null_terminate=True):
    """ Create a ctypes buffer from a string or list. """
    if type(buf) is unicode:
        buf = str(buf)
    if type(buf) is str:
        if buf.startswith("0x"):
            if buf.count(','):
                buf = "".join([chr(int(a[2:], 16)) for a in buf.split(',')])
            else:
                buf = buf[2:]
                buf = "".join([chr(int(buf[n:n+2], 16)) for n in range(0, len(buf), 2)])
        elif not null_terminate:
            return create_string_buffer(buf, len(buf))
        return create_string_buffer(buf)
    elif type(buf) is list:
        return create_string_buffer("".join([chr(n) for n in buf]))
    elif buf is None:
        return (c_char * 0)()
    elif hasattr(buf,"_type_") and hasattr(buf, "__sizeof__") and (buf._type_ is c_uint8 or buf._type_ is c_char):
        return buf # Nothing to do
    else:
        raise Exception("Invalid scan ID field, not string or list of numbers")


def str_from_c_buffer(buf):
    """ Create a string from a ctypes buffer. """
    return ",".join(["0x%02x" % ord(c) for c in buf])


def set_log_file(f):
    global _log_file
    if f is not None:
        _set_log_fd(f.fileno())
        _log_file = f
        # _log_file is to hold a reference to the file object so the GC doesn't close the fd we are now logging to.
    else:
        _set_log_fd(2) #stderr
        _log_file = None

# Executed on import
if not _devtank_ready():
    global _msg_stream, _log_file
    _devtank_init()
    _msg_stream = sys.stdout
    atexit.register(_devtank_shutdown)
    _log_file = None
