import os
import sys
import atexit
import time
import datetime
import subprocess


_ANSI_RED     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_DEFAULT = "\x1B[39m"

# No C file, so use python functions

dt_usecs = int

get_current_us = lambda: dt_usecs(time.time_ns / 1000.)

_devtank_is_ready = False

def _devtank_init():
    global _devtank_is_ready
    _devtank_is_ready = True

def _devtank_ready():
    global _devtank_is_ready
    return _devtank_is_ready

def _devtank_shutdown():
    global _devtank_is_ready
    _devtank_is_ready = False

def _set_log_fd(fd):
    global log_fd
    log_fd = fd

def _get_log_fd():
    global log_fd
    if "log_fd" not in globals():
        log_fd = None
    if log_fd is None:
        log_fd = sys.stderr.fileno()
    return log_fd

def _log_msg(fd: int, msg: str, colour: str = _ANSI_DEFAULT):
    if os.isatty(fd):
        pl = f"{colour}{datetime.datetime.now().strftime('%d/%m %T.%f')} [{os.getpid()}] {msg}{_ANSI_DEFAULT}\n"
    else:
        pl = f"{datetime.datetime.now().strftime('%d/%m %T.%f')} [{os.getpid()}] {msg}\n"
    return os.write(fd, pl.encode())

_error_msg          = lambda *x: _log_msg(_get_log_fd(), f"ERROR: {str(*x)}", colour=_ANSI_RED)
_warning_msg        = lambda *x: _log_msg(_get_log_fd(), f"WARNING: {str(*x)}", colour=_ANSI_RED)
_info_msg           = lambda *x: _log_msg(_get_log_fd(), f"INFO: {str(*x)}")
error_msg           = _error_msg
warning_msg         = _warning_msg
info_msg            = _info_msg
def enable_info_msgs(enable: bool):
    info_msg = _info_msg if enable else lambda *x: None
def enable_warning_msgs(enable: bool):
    warning_msg = _warning_msg if enable else lambda *x: None
info_msgs_is_enabled = lambda: info_msg is _info_msg

def dt_get_build_info():
    cmd_get_commit = "git log -n 1 --format=\"%h-%f\""
    gitcommit = subprocess.check_output(cmd_get_commit.split()).decode().strip()
    # There is no 'build date' so I will use the date of the last commit
    # Fri 15 Dec 12:39:32 UTC 2023
    cmd_get_date = "date --date=@`git log -n 1 --pretty=format:%at`"
    buildtime = subprocess.check_output(cmd_get_date, env={"TZ": "UTC0"}, shell=True).decode().strip()
    return buildtime, gitcommit

## Convert C microseconds into seconds with fractions.
dt_usecs_to_secs = lambda x : x / 1000000.0

## Convert seconds with fractions into C microseconds.
secs_to_dt_usecs = lambda x : dt_usecs(int(x * 1000000))

# Public exports

## Microseconds in a second
USEC_SECOND = 1000000
## Microseconds in a minute.
USEC_MINUTE = (USEC_SECOND * 60)


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

# Executed on import
if not _devtank_ready():
    global _msg_stream, _msg_stream_write, _log_file
    _devtank_init()
    _msg_stream = sys.stdout
    _msg_stream_write = _msg_stream.write
    atexit.register(_devtank_shutdown)
    _log_file = None
