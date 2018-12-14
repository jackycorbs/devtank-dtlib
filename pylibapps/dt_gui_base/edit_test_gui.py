from dt_gui_base import populate_test_properties

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


_properties = {}


def _clicked_cancel(window, context):
    global _properties

    _properties = {}
    context.pop_view()


def _clicked_ok(window, context):
    global _properties

    for value in _properties.values():
        value.pop("widget_dict")

    context.db.set_defaults(_properties)

    _clicked_cancel(window, context)



def open_edit_test_page(context, test):
    global _properties

    test_props = context.builder.get_object("TestDefaultList")
    filename = test.get_file_to_local()
    _properties = {}

    populate_test_properties(context, test_props, filename, _properties)

    context.push_view()
    context.change_view("TestDefaults")


def init_edit_test_page(context):

    window = context.builder.get_object("TestDefaults")

    done_btn = context.builder.get_object("edit_test_done_btn")
    cancel_btn = context.builder.get_object("edit_test_cancel_btn")

    done_btn.connect("clicked", lambda x: _clicked_ok(window, context))
    cancel_btn.connect("clicked", lambda x: _clicked_cancel(window, context))
