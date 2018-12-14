
from notify_gui import open_notify_gui

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def _clicked_back(tests_group, builder, name_entry, desc_text, context):
    tests_group.name = name_entry.get_text()
    buf = desc_text.get_buffer()
    tests_group.description = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

    context.change_view("TestGroupProperties")


def _clicked_ok(tests_group, context, name_entry, desc_text):
    tests_group.name = name_entry.get_text()
    buf = desc_text.get_buffer()
    tests_group.description = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
    builder = context.builder
    if not len(tests_group.name):
        open_notify_gui(context, "No name set")
        return
    if not len(tests_group.description):
        open_notify_gui(context, "No description set")
        return

    if not tests_group.db_group:
        for group in tests_group.db.get_groups():
            if group.name == tests_group.name:
                open_notify_gui(context, "Test group name already in use")
                return

    tests_group.updated_db()

    context.pop_view()


def _show_naming(name_entry, desc_text, tests_group):
    name_entry.set_text(tests_group.name)
    desc_text.get_buffer().set_text(tests_group.description)


def open_test_group_naming(context):
    context.change_view("TestGroupNaming")


def init_test_group_naming(context):
    
    tests_group = context.tests_group
    builder = context.builder

    window = builder.get_object("TestGroupNaming")

    back_btn = builder.get_object("naming_back_btn")
    ok_btn = builder.get_object("naming_ok_btn")

    name_entry = builder.get_object("naming_name_entry")
    desc_text = builder.get_object("naming_desc_text")

    back_btn.connect("clicked", lambda x: _clicked_back(tests_group, builder, name_entry, desc_text, context))
    ok_btn.connect("clicked", lambda x: _clicked_ok(tests_group, context, name_entry, desc_text))

    window.connect("show", lambda x: _show_naming(name_entry, desc_text, tests_group))
