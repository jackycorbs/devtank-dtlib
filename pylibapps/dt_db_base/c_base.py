import os
from ctypes import *
import sys
import atexit

_c_libcbase = cdll.LoadLibrary("libbase.so")

def c_base_func(c_lib, restype, name, argtypes):
    """Export C function from shared C library."""
    r = getattr(c_lib, name)
    r.restype = restype
    r.argtypes = argtypes
    return r


def _c_libbase_func(restype, name, argtypes):
    return c_base_func(_c_libcbase, restype, name, argtypes)

_ANSI_RED     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_DEFAULT = "\x1B[39m"


# Public imports

## Enable info messages to log.
enable_info_msgs     = _c_libbase_func(None,   "enable_info_msgs",     (c_bool,))
## Enable warning messages to log.
enable_warning_msgs  = _c_libbase_func(None,   "enable_warning_msgs",  (c_bool,))
## Is info messages going to log.
info_msgs_is_enabled = _c_libbase_func(c_bool, "info_msgs_is_enabled", None)

## Type used to hand C functions microseconds.
dt_usecs = c_int64

## Convert C microseconds into seconds with fractions.
dt_usecs_to_secs = lambda x : x / 1000000.0

## Convert seconds with fractions into C microseconds.
secs_to_dt_usecs = lambda x : dt_usecs(int(x * 1000000))

# Private imports

## Get the build information of C library.
## @param build_time Time/Data the C library was built.
## @param git_commit string of the git SHA1 when built.
_dt_get_build_info = _c_libbase_func(None,   "dt_get_build_info", (POINTER(c_char_p), POINTER(c_char_p)))
_devtank_init      = _c_libbase_func(None,   "devtank_init",      None)
_devtank_ready     = _c_libbase_func(c_bool, "devtank_ready",     None)
_devtank_shutdown  = _c_libbase_func(None,   "devtank_shutdown",  None)
_error_msg         = _c_libbase_func(None,   "error_msg",         (c_char_p,))
_warning_msg       = _c_libbase_func(None,   "warning_msg",       (c_char_p,))
_info_msg          = _c_libbase_func(None,   "info_msg",          (c_char_p,))
_set_log_fd        = _c_libbase_func(None,   "set_log_fd",        (c_int,))
_get_log_fd        = _c_libbase_func(c_int,  "get_log_fd",        None)

# Public exports

## Microseconds in a second
USEC_SECOND = 1000000
## Microseconds in a minute.
USEC_MINUTE = (USEC_SECOND * 60)

_to_bytes_msg = lambda msg : msg if isinstance(msg, bytes) else msg.encode()
error_msg     = lambda msg : _error_msg(_to_bytes_msg(msg).replace(b'%',b'%%'))
warning_msg   = lambda msg : _warning_msg(_to_bytes_msg(msg).replace(b'%',b'%%'))
info_msg      = lambda msg : _info_msg(_to_bytes_msg(msg).replace(b'%',b'%%'))


def output_bad(msg):
    """ Output information about a fail case. """
    if _msg_stream.isatty():
        _msg_stream_write(_ANSI_RED)
        _msg_stream_write(msg)
        _msg_stream_write(_ANSI_DEFAULT)
        _msg_stream_write("\n")
    else:
        _msg_stream_write("BAD: ")
        _msg_stream_write(msg)
        _msg_stream_write("\n")
    _msg_stream.flush()
    lines = msg.splitlines()
    warning_msg("Python bad output: " + lines[0] if len(lines) else "")

def output_good(msg):
    """ Output information about a success case. """
    if _msg_stream.isatty():
        _msg_stream_write(_ANSI_GREEN)
        _msg_stream_write(msg)
        _msg_stream_write(_ANSI_DEFAULT)
        _msg_stream_write("\n")
    else:
        _msg_stream_write("Good: ")
        _msg_stream_write(msg)
        _msg_stream_write("\n")
    _msg_stream.flush()
    lines = msg.splitlines()
    info_msg("Python good output: " + lines[0] if len(lines) else "")

def output_normal(msg):
    _msg_stream_write(msg)
    _msg_stream_write("\n")
    _msg_stream.flush()
    lines = msg.splitlines()
    info_msg("Python normal output: " + lines[0] if len(lines) else "")

def set_output(sink):
    global _msg_stream, _msg_stream_write
    if sink:
        assert hasattr(sink, "write") and hasattr(sink, "isatty")
        _msg_stream = sink
        if hasattr(_msg_stream, "encoding"):
            _msg_stream_write = _msg_stream.write
        else:
            _msg_stream_write = lambda msg : _msg_stream.write(msg.encode())
    else:
        _msg_stream = sys.stdout
        _msg_stream_write = _msg_stream.write

def set_log_file(f):
    global _log_file
    if f is not None:
        _set_log_fd(f.fileno())
        _log_file = f
        # _log_file is to hold a reference to the file object so the GC doesn't close the fd we are now logging to.
    else:
        _set_log_fd(2) #stderr
        _log_file = None


def dt_get_build_info():
    buildtime = c_char_p()
    gitcommit = c_char_p()
    _dt_get_build_info(byref(buildtime), byref(gitcommit))
    return buildtime.value, gitcommit.value

# Executed on import
if not _devtank_ready():
    global _msg_stream, _msg_stream_write, _log_file
    _devtank_init()
    _msg_stream = sys.stdout
    _msg_stream_write = _msg_stream.write
    atexit.register(_devtank_shutdown)
    _log_file = None
