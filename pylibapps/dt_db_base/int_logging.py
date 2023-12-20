import os
import time
import logging


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
    def __init__(self, use_colour, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colour = use_colour

    def _format_colour(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.datefmt   = "%Y-%m-%dT%H:%M:%S"
        formatter.converter = time.gmtime
        return formatter.format(record)

    def _format_no_colour(self, record):
        formatter = logging.Formatter(self.FORMAT)
        formatter.datefmt   = "%Y-%m-%dT%H:%M:%S"
        formatter.converter = time.gmtime
        return formatter.format(record)

    @property
    def use_colour(self):
        return self._use_colour

    @use_colour.setter
    def use_colour(self, val):
        self._use_colour = val
        self.format = self._format_colour if self._use_colour else self._format_no_colour


def get_logger(name, log_file=None):
    level = logging.DEBUG if "DEBUG" in os.environ else logging.INFO
    logger        = logging.getLogger(name)
    logger.setLevel(level)
    formatter           = _logging_formatter_t(log_file is None)
    if log_file:
        streamhandler   = logging.FileHandler(log_file)
    else:
        streamhandler   = logging.StreamHandler()
    streamhandler.setLevel(level)
    streamhandler.setFormatter(formatter)
    logger.addHandler(streamhandler)
    return logger
