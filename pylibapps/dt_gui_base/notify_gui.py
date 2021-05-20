

_singleton = None


class notify_object(object):
    def __init__(self, context):
        self.context = context
        self._exit_cb = None
        self.notift_ok_btn = context.builder.get_object("notift_ok_btn")
        self.notify_lab = context.builder.get_object("notify_lab")
        self.notift_ok_btn.connect("clicked", lambda x: self._response_click())

    def _response_click(self):
        self.context.pop_view()
        if self._exit_cb:
            self._exit_cb()

    def open(self, msg, cancel_btn=False, exit_cb=None):
        context = self.context
        context.push_view()
        context.change_view("UserNotify")
        self.notift_ok_btn.set_label("gtk-cancel" if cancel_btn else "gtk-ok")
        self.notify_lab.set_text(msg)
        self._exit_cb = exit_cb



def open_notify_gui(context, msg, cancel_btn=False, exit_cb=None):
    _singleton.open(msg, cancel_btn, exit_cb)


def init_notify_gui(context):
    global _singleton
    _singleton = notify_object(context)
