
_exit_cb = None

def _response_click(context):
    context.pop_view()
    if _exit_cb:
        _exit_cb()


def open_notify_gui(context, msg, cancel_btn=False, exit_cb=None):
    context.push_view()
    context.change_view("UserNotify")
    notift_ok_btn = context.builder.get_object("notift_ok_btn")
    notift_ok_btn.set_label("gtk-cancel" if cancel_btn else "gtk-ok")
    notify_lab = context.builder.get_object("notify_lab")
    notify_lab.set_text(msg)
    global _exit_cb
    _exit_cb = exit_cb


def init_notify_gui(context):
    builder = context.builder
    notift_ok_btn = builder.get_object("notift_ok_btn")
    notift_ok_btn.connect("clicked", lambda x: _response_click(context))
