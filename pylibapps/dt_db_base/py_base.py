import os
import sys
import atexit
import time
import datetime
import logging
import subprocess

""" This is to toggle the use of the python logging library """
__USE_LOGGING__ = False


_ANSI_RED     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_DEFAULT = "\x1B[39m"

class _logging_formatter_t(logging.Formatter):
    RED         = "\033[31;20m"
    GREEN       = "\033[32;20m"
    YELLOW      = "\033[33;20m"
    BLUE        = "\033[34;20m"
    MAGENTA     = "\033[35;20m"
    CYAN        = "\033[36;20m"
    GREY        = "\033[37;20m"
    WHITE       = "\033[39:20m"
    BOLD_RED    = "\033[31;1m"
    RESET       = WHITE
    FORMAT      = "%(asctime)s.%(msecs)03d [%(thread)s] %(levelname)s: %(message)s"
    DATEFMT     = "%d/%m %T"

    FORMATS = {
        logging.DEBUG:    GREY     + FORMAT + RESET,
        logging.INFO:     WHITE    + FORMAT + RESET,
        logging.WARNING:  YELLOW   + FORMAT + RESET,
        logging.ERROR:    RED      + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET
    }

    def _format_colour(self, record):
        #log_fmt = self.FORMATS.get(record.levelno)
        #formatter = logging.Formatter(log_fmt)
        formatter = super(self.FORMAT)
        formatter.datefmt   = "%d/%m %T"
        formatter.converter = time.gmtime
        return formatter.format(record)

    def _format_no_colour(self, record):
        formatter = logging.Formatter(self.FORMAT)
        formatter.datefmt   = "%d/%m %T"
        formatter.converter = time.gmtime
        return formatter.format(record)

    def colour(self, enabled):
        if enabled:
            self.format = self._format_colour
        else:
            self.format = self._format_no_colour

class _logging_stream_handler_less_than_filter(logging.Filter):
    def __init__(self, exclusive_maximum, name=""):
        super(_logging_stream_handler_less_than_filter, self).__init__(name)
        self.max_level = exclusive_maximum
    def filter(self, record):
        return 1 if record.levelno < self.max_level else 0

#global logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)

_formatter = _logging_formatter_t()
is_a_tty = os.isatty(sys.stdout.fileno())

_formatter.colour(is_a_tty)

if is_a_tty:
    _stdout_handler = logging.StreamHandler(sys.stdout)
    _stdout_handler.setLevel(logging.INFO)
    _stdout_handler.addFilter(_logging_stream_handler_less_than_filter(logging.WARNING))
    _stdout_handler.setFormatter(_formatter)

    _stderr_handler = logging.StreamHandler(sys.stderr)
    _stderr_handler.setLevel(logging.WARNING)
    _stderr_handler.setFormatter(_formatter)
    logger.addHandler(_stdout_handler)
    logger.addHandler(_stderr_handler)

else:
    _file_handler = logging.FileHandler() # TODO: This needs to have the log file location in I think...
    _file_handler.setLevel(logging.INFO)
    _file_handler.addFormatter(_formatter)
    logger.addHandler(_file_handler)

# No C file, so use python functions

dt_usecs = int

get_current_us = lambda: dt_usecs(time.time_ns / 1000.)

log_fd = sys.stderr.fileno()
out_fd = sys.stdout.fileno()

_devtank_init       = lambda: None
_devtank_ready      = lambda: True
_devtank_shutdown   = lambda: None

if __USE_LOGGING__:
    error_msg           = lambda *x: logger.error(*x)
    warning_msg         = lambda *x: logger.warning(*x)
    info_msg            = lambda *x: logger.info(*x)
    enable_info_msgs = lambda x: logger.setLevel(logging.INFO)
    enable_warning_msgs = lambda x: logger.setLevel(logging.WARNING)
    info_msgs_is_enabled = lambda: logger.level <= logging.INFO
else:
    _error_msg          = lambda *x: print(f"{_ANSI_RED}ERROR:", *x, _ANSI_DEFAULT)
    _warning_msg        = lambda *x: print(f"{_ANSI_RED}WARNING:", *x, _ANSI_DEFAULT)
    _info_msg           = lambda *x: print("INFO:", *x, _ANSI_DEFAULT)
    error_msg           = _error_msg
    warning_msg         = _warning_msg
    info_msg            = _info_msg
    def enable_info_msgs(enable: bool):
        info_msg = _info_msg if enable else lambda *x: None
    def enable_warning_msgs(enable: bool):
        warning_msg = _warning_msg if enable else lambda *x: None
    info_msgs_is_enabled = lambda: info_msg is _info_msg

def _set_log_fd(fd):
    log_fd = fd
_get_log_fd         = lambda: log_fd

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
    global _msg_stream, _msg_stream_write, _log_file
    _devtank_init()
    _msg_stream = sys.stdout
    _msg_stream_write = _msg_stream.write
    atexit.register(_devtank_shutdown)
    _log_file = None
