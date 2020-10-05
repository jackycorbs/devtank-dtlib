#! /usr/bin/python3

import os
import sys
import datetime
import argparse
import thread
import yaml
import types

import dt_db_base
import dt_cli_base
import example_lib

parser = argparse.ArgumentParser(description='Command line interface for Example tester')
parser.add_argument('-v','--verbose', help='Increase log information', action='store_true')
parser.add_argument('--config', help='DB config file to use', type=str)
parser.add_argument('command', help='command followed by arguments.', nargs='*')


cmds = dt_cli_base.generic_cmds.copy()


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
        example_lib.enable_info_msgs(True)

    if args['config']:
        db_def_file = args['config']
    else:
        db_def_file = "config_sqlite_db.yaml"

    with open(db_def_file) as f:
        db_def = yaml.load(f, Loader=yaml.FullLoader)

    db_def['sql'] = example_lib.example_sql_common()
    db_def["fn_get_dev"] = example_lib.db_example_dev.get_by_uuid
    db_def["work_folder"] = os.path.abspath("../gui/files_cache")
    db_def["open_db_backend"] = example_lib.base_open_db_backend

    context = dt_db_base.base_context_object(args, db_def)

    context.db_init()

    assert context.db, "No database"

    dt_cli_base.execute_cmd(context, cmd, cmd_args, cmds)



if __name__ == "__main__":
    main()
