#! /usr/bin/python3

import os
import sys
import datetime
import argparse
import yaml
import types

import dt_db_base
import dt_cli_base
import example_lib

parser = argparse.ArgumentParser(description='Command line interface for Example tester')
parser.add_argument('-v','--verbose', help='Increase log information', action='store_true')
parser.add_argument('--config', help='DB config file to use', type=str)
parser.add_argument('command', help='command followed by arguments.', nargs='*')

_debug_messages = False

cmds = dt_cli_base.generic_cmds.copy()


_ANSI_RED     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_WARN    = "\x1B[33m"
_ANSI_DEFAULT = "\x1B[39m"


def print_line(colorcode, msg):
    sys.stdout.write(colorcode + msg + _ANSI_DEFAULT)


def run_group(context, cmd_args):
    import gi
    gi.require_version('GLib', '2.0')
    from gi.repository import GLib

    assert len(cmd_args) > 1, "run_group takes twos argument, the group name and device serial"
    group_name = " ".join(cmd_args[0:-1])
    dev_serial = cmd_args[-1]

    db_dev = example_lib.db_example_dev.get_by_serial(context.db, dev_serial)
    if not db_dev:
        db_dev = example_lib.db_example_dev.create(context.db, dev_serial, "UNSET")
        db_dev.update_uuid("<unknown>-%u" % db_dev.id)
    context.devices = [db_dev]

    db_group = context.db.get_group(group_name)
    if not db_group:
        print("Failed to find tests group.")
        sys.exit(-1)
    context.tests_group.populate_from(db_group)
    loop = GLib.MainLoop()
    run_group_man = dt_db_base.default_run_group_manager(context,
                                                    lambda msg : print_line(_ANSI_GREEN, msg),
                                                    lambda msg : print_line(_ANSI_RED, msg),
                                                    lambda msg : print_line(_ANSI_DEFAULT, msg),
                                                    lambda msg : print_line(_ANSI_DEFAULT, msg) if _debug_messages else None,
                                                    lambda msg : print_line(_ANSI_WARN, msg) if _debug_messages else None,
                                                    lambda msg : print_line(_ANSI_RED, msg) if _debug_messages else None,
                                                    { "FINISHED" : lambda args: loop.quit() } )
    print("=" * 72)
    if run_group_man.start():
        loop.run()
        run_group_man.wait_for_end()
    else:
        print("Failed to start tests group.")
    print("=" * 72)


cmds["run_group"] = (run_group, "Run group <name> on attached hardware.")



def main():

    print("Command Line Example Tester", datetime.datetime.utcnow())

    args = vars(parser.parse_args())

    cmd = args['command']
    cmd_args = cmd[1:]
    cmd = cmd[0] if len(cmd) else None

    if cmd is None:
        parser.print_help()
        print("\n")
        dt_cli_base.print_cmd_help(cmds)
        sys.exit(-1)

    if args['verbose']:
        global _debug_messages
        example_lib.enable_info_msgs(True)
        _debug_messages = True

    if args['config']:
        db_def_file = args['config']
    else:
        db_def_file = "config_sqlite_db.yaml"

    with open(db_def_file) as f:
        db_def_gen = yaml.safe_load_all(f)
        db_def = [root for root in db_def_gen][0]

    db_def['sql'] = example_lib.example_sql_common()
    db_def["fn_get_dev"] = example_lib.db_example_dev.get_by_uuid
    db_def["work_folder"] = os.path.abspath("../gui/files_cache")
    db_def["open_db_backend"] = example_lib.base_open_db_backend

    context = example_lib.cli_context_object(args, db_def)

    context.db_init()

    assert context.db, "No database"

    dt_cli_base.execute_cmd(context, cmd, cmd_args, cmds)



if __name__ == "__main__":
    main()
