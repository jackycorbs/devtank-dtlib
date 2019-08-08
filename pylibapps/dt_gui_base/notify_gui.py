
def _response_click(context):
    context.pop_view()


def open_notify_gui(context, msg, cancel_btn=False):
    context.push_view()
    context.change_view("UserNotify")
    notift_ok_btn = context.builder.get_object("notift_ok_btn")
    notift_ok_btn.set_label("gtk-cancel" if cancel_btn else "gtk-ok")
    notify_lab = context.builder.get_object("notify_lab")
    notify_lab.set_text(msg)


def init_notify_gui(context):
    builder = context.builder
    notift_ok_btn = builder.get_object("notift_ok_btn")
    notift_ok_btn.connect("clicked", lambda x: _response_click(context))
