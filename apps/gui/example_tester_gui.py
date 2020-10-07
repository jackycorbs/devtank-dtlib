#! /usr/bin/python3

import os
import datetime
import argparse
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
parser.add_argument('--admin', help='Show Test Groups', action='store_true')
parser.add_argument('--config', help='DB config file to use', type=str)


def get_schema():
    schema_base = example_lib_gui.resources["db_base.sql"]
    schema = example_lib_gui.resources["db.sql"]

    return schema_base + ";" + schema


def db_load_extra(db):
    tests = db.get_all_tests()
    if not len(tests):
        print("Import tests")
        db.add_tests_folder(os.path.abspath("tests"))
        db.load_groups(os.path.abspath("tests/groups.yaml"))


def main():

    print("Running Example Tester GUI", datetime.datetime.utcnow())

    args = vars(parser.parse_args())

    if args['verbose']:
        example_lib.enable_info_msgs(True)

    builder = Gtk.Builder()
    builder.add_from_string(example_lib_gui.resources['gui_base.glade'])
    builder.add_from_string(example_lib_gui.resources['gui.glade'])

    if args['config']:
        db_def_file = args['config']
    else:
        db_def_file = "config_sqlite_db.yaml"

    with open(db_def_file) as f:
        db_def_gen = yaml.safe_load_all(f)
        db_def = [root for root in db_def_gen][0]

    db_def['sql'] = example_lib.example_sql_common()
    db_def["fn_get_dev"] = example_lib.db_example_dev.get_by_uuid
    db_def["work_folder"] = os.path.abspath("files_cache")
    db_def["open_db_backend"] = example_lib.base_open_db_backend
    db_def["fn_get_schema"] = get_schema
    db_def["fn_extra_load"] = db_load_extra

    context = example_lib_gui.gui_context_object(args, db_def, builder)

    example_lib_gui.init(context)

    example_lib_gui.open_start_page(context)
    if args['admin']:
        example_lib_gui.open_groups_list(context)

    main_window = context.builder.get_object("main_window")

    main_window.connect("destroy", lambda x: context.close_app())

    if not args['desktop']:
        context.fullscreen()

    main_window.show()

    if args['production'] and not args['desktop']:
        cursor = Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR)
        main_window.get_window().set_cursor(cursor)

    Gtk.main()


if __name__ == "__main__":
    main()
