from dt_gui_base import populate_test_properties, update_default

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def _clicked_ok(context):
    context.pop_view()


def _clicked_undo(context):
    deleted_tests_list = context.builder.get_object("deleted_tests_list")
    selection = deleted_tests_list.get_selection()
    model, treeiters = selection.get_selected_rows()
    for treeiter in treeiters:
        test = model[treeiters][1]
        test.restore()
        model.remove(model.get_iter(treeiter))


def _add_new_test(context, file_btn, properties):
    filename = file_btn.get_filename()
    if not len(filename):
        return

    for prop_name in properties:
        update_default(properties[prop_name])

    for value in properties.values():
        value.pop("widget_dict", None)

    now = db_ms_now()

    with context.db.db as c:
        context.db.add_defaults(properties, c, now)
        context.db.add_test(filename, c, now)

    file_btn.set_filename("")
    test_props = context.builder.get_object("NewTestProps")
    old_props = test_props.get_children()
    for child in old_props:
        test_props.remove(child)
    context.tests_group.update_defaults()


def _new_file_selected(context, filename, properties):
    test_props = context.builder.get_object("NewTestProps")

    try:
        populate_test_properties(context, test_props, filename, properties)
    except Exception as e:
        from dt_gui_base import open_notify_gui
        file_btn = context.builder.get_object("test_file_btn")
        file_btn.set_filename("")
        open_notify_gui(context, "Failed loading new test file:\n%s" % str(e))


def _show_test_page(context):
    deleted_tests_list = context.builder.get_object("deleted_tests_list")
    deleted_tests_list_store = deleted_tests_list.get_model()

    tests = context.db.get_deleted_tests()
    deleted_tests_list_store.clear()

    for test in tests:
        deleted_tests_list_store.append([test.name, test])


def open_new_test_page(context):
    context.push_view()
    context.change_view("AddTest")


def init_new_test_page(context):

    window = context.builder.get_object("AddTest")

    deleted_tests_list = context.builder.get_object("deleted_tests_list")

    deleted_tests_list_store = Gtk.ListStore(str, object)
    deleted_tests_list.set_model(deleted_tests_list_store)
    deleted_tests_list.append_column(Gtk.TreeViewColumn("Test", Gtk.CellRendererText(), text=0))

    add_test_done_btn = context.builder.get_object("add_test_done_btn")
    add_test_undo_btn = context.builder.get_object("test_undo_btn")
    add_test_add_btn = context.builder.get_object("test_add_btn")
    file_btn = context.builder.get_object("test_file_btn")

    add_test_done_btn.connect("clicked", lambda x: _clicked_ok(context))
    add_test_undo_btn.connect("clicked", lambda x: _clicked_undo(context))

    properties = {}

    file_btn.connect("file-set", lambda x: _new_file_selected(context, x.get_filename(), properties))
    
    add_test_add_btn.connect("clicked", lambda x: _add_new_test(context, file_btn, properties))

    window.connect("show", lambda win: _show_test_page(context))
