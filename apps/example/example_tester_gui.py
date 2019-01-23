#! /usr/bin/python

import os
import datetime
import argparse
import thread
import yaml
import types

import example_lib
import example_lib_gui

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib


parser = argparse.ArgumentParser(description='Graphical interface for Example tester')
parser.add_argument('-v','--verbose', help='Increase log information', action='store_true')
parser.add_argument('--desktop', help='Running on a desktop', action='store_true')
parser.add_argument('--production', help='Hide advanced and quit.', action='store_true')


def get_schema():
    schema = example_lib.resources["db.sql"]

    # Break into statements
    schema = schema.split(';')

    # Drop transaction begin/end and commit
    return schema[1:-2]


def main():

    print "Running Example Tester GUI", datetime.datetime.utcnow()

    args = vars(parser.parse_args())

    if args['verbose']:
        example_lib.enable_info_msgs(True)

    builder = Gtk.Builder()
    builder.add_from_string(example_lib.resources['gui_base.glade'])
    builder.add_from_string(example_lib.resources['gui.glade'])

    db_def_file = "config_sqlite_db.yaml"

    with open(db_def_file) as f:
        db_def = yaml.load(f)

    work_folder = os.path.abspath("files_cache")

    db_def['sql'] = example_lib.example_sql_common()

    db = example_lib.base_open_db_backend(db_def, get_schema, work_folder)

    tests = db.get_all_tests()
    if not len(tests):
        print "Import tests"
        db.add_tests_folder(os.path.abspath("tests"))
        db.load_groups(os.path.abspath("tests/groups.yaml"))

    db.get_dev = types.MethodType(lambda db, uuid: example_lib.db_example_dev.get_by_uuid(db, uuid), db, db.__class__)

    context = example_lib_gui.gui_context_object(args, db, builder)

    example_lib_gui.init(context)

    example_lib_gui.open_start_page(context)

    main_window = context.builder.get_object("main_window")

    main_window.connect("destroy", lambda x: context.close_app())

    if not args['desktop']:
        context.fullscreen()

    main_window.show()

    if args['production']:
        cursor = Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR)
        main_window.get_window().set_cursor(cursor)

    Gtk.main()


if __name__ == "__main__":
    main()
