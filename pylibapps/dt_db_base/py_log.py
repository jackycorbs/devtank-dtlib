from .c_base import error_msg, warning_msg, info_msg


def dt_py_log_hook_init():
    import logging

    class dt_py_log_hook_t(logging.Handler):
        def __init__(self):
            logging.Handler.__init__(self)
            log = logging.getLogger()
            log.setLevel(logging.DEBUG)

        def emit(self, record):
            if isinstance(record.msg, str) and (isinstance(record.args, list) or isinstance(record.args, tuple)):
                msg = 'PyLog: [%s] : "%s"' % (record.module, record.msg % record.args)
            else:
                msg = 'PyLog: [%s] : "%s"' % (record.module, record.msg)
            if record.levelno < 30:
                info_msg(msg)
            elif record.levelno < 40:
                warning_msg(msg)
            else:
                error_msg(msg)

    log = logging.getLogger()
    log.addHandler(dt_py_log_hook_t())
