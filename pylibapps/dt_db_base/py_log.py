from __future__ import print_function, absolute_import
from .c_base import error_msg, warning_msg, info_msg


def dt_py_log_hook_init():
    import logging

    class dt_py_log_hook_t(logging.Handler):
        def __init__(self):
            logging.Handler.__init__(self)
            log = logging.getLogger()
            log.setLevel(logging.DEBUG)

        def emit(self, record):
            msg = '<%s> "%s"' % (record.module, record.msg)
            if record.levelno < 30:
                info_msg(msg)
            elif record.levelno < 40:
                warning_msg(msg)
            else:
                error_msg(msg)

    log = logging.getLogger()
    log.addHandler(dt_py_log_hook_t())
