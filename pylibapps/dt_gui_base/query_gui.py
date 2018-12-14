
class _user_query_singleton(object):
    def __init__(self, context):
        self.return_cb = None
        self.context = context
        builder = context.builder
        self.query_lab = builder.get_object("query_lab")
        query_yes_btn = builder.get_object("query_yes_btn")
        query_no_btn  = builder.get_object("query_no_btn")

        query_yes_btn.connect("clicked", lambda x: self.response_click(True))
        query_no_btn.connect("clicked",  lambda x: self.response_click(False))

    def do(self, msg, return_cb):
        self.query_lab.set_text(msg)
        self.return_cb = return_cb
        self.context.push_view()
        self.context.change_view("UserQuery")

    def response_click(self, yes_no):
        self.context.pop_view()
        if self.return_cb:
            self.return_cb(yes_no)


global _user_query


def open_query_gui(msg, return_cb):
    global _user_query
    _user_query.do(msg, return_cb)


def init_query_gui(context):
    global _user_query
    _user_query = _user_query_singleton(context)
