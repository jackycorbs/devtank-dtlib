import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class _user_query_singleton(object):
    def __init__(self, context):
        self.return_cb = None
        self.msg = None
        self.context = context
        self.builder = context.builder
        self.query_lab = self.builder.get_object("query_lab")
        self.query_yes_btn_box = self.builder.get_object("query_yes_btn_box")
        self.query_no_btn_box = self.builder.get_object("query_no_btn_box")
        self.query_yes_btn = self.builder.get_object("query_yes_btn")
        self.query_no_btn  = self.builder.get_object("query_no_btn")

        self.query_yes_btn.connect("clicked", lambda x: self.response_click(True))
        self.query_no_btn.connect("clicked",  lambda x: self.response_click(False))

    def do(self, msg, return_cb):
        self.msg = msg
        self.query_lab.set_text(msg)
        self.return_cb = return_cb
        self.invert_button_positions()
        self.context.push_view()
        self.context.change_view("UserQuery")

    def invert_button_positions(self):
        current_pack_type = self.query_yes_btn_box.query_child_packing(self.query_yes_btn)[3]
        if current_pack_type == Gtk.PackType.START:
            target_pack_type = Gtk.PackType.END
        else:
            target_pack_type = Gtk.PackType.START

        self.query_yes_btn_box.set_child_packing(self.query_yes_btn, False, True, 30, target_pack_type)
        self.query_no_btn_box.set_child_packing(self.query_no_btn, False, True, 30, target_pack_type)


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
