from __future__ import print_function
import os
import sys
import yaml
import datetime
import dt_db_base


def list_groups(context, cmd_args):
    groups = context.db.get_groups()
    for group in groups:
        print("Group : %s - %s" % ("%25s" % group.name, group.desc))


def update_tests(context, cmd_args):
    assert len(cmd_args) == 1, "Wrong argument count."

    groups_file = os.path.abspath(cmd_args[0])

    with open(groups_file) as f:
        groups_defs_gen =yaml.safe_load_all(f)
        groups_defs = [root for root in groups_defs_gen][0]

    db = context.db
    c = db.db.cursor()
    now = dt_db_base.db_ms_now()

    groups = groups_defs['groups']
    for group in groups:
        name = group['name']
        db_group = db.get_group(name)
        while db_group:
            print("Deleting existing '%s'" % name)
            tests = db_group.get_tests()
            for test in tests:
                test.remove(c, now)
            db_group.delete(c, now)
            db_group = db.get_group(name)

    print("Loading new version of groups.")
    db.load_groups(groups_file, c, now)
    db.db.commit()


def group_results(context, cmd_args):
    assert len(cmd_args) > 0, "Wrong argument count."
    group_name = " ".join(cmd_args)
    db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)
    print("Group has %u result sessions." % db_group.get_all_sessions_count())


def print_session(session):
    print("=" * 72)
    print("Time :", datetime.datetime.utcfromtimestamp(session.time_of_tests).strftime('%Y-%m-%d %H:%M:%S'))
    print("Overall :", "passed" if session.pass_fail else "FAILED")
    print("Session :", session.id)
    for dev_uuid, dev_results in session.devices.items():
        dev = session.db.get_dev(dev_uuid)
        if dev_uuid != dev.serial_number:
            print("Device : %s, %s" % (dev_uuid, dev.serial_number))
        else:
            print("Device : ", dev_uuid)

        for result in dev_results.results:
            if len(result):
                print('Test : "%s" (Output File:%s, Log File:%s) - %s' % (
                        result[1],
                        "%u" % result[2] if result[2] else "NONE",
                        "%u" % result[3] if result[3] else "NONE",
                        "passed" if result[0] else "FAILED"))


def group_result(context, cmd_args):
    assert len(cmd_args) > 0, "Wrong argument count."
    group_name = " ".join(cmd_args[:-1])
    db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)
    session_index = int(cmd_args[-1])
    sessions = db_group.get_all_sessions(session_index, 1)
    if not sessions:
        print("Result session not found of index %u" % session_index)
        sys.exit(-1)

    print_session(sessions[0])


def group_dump(context, cmd_args):
    assert len(cmd_args) > 0, "Wrong argument count."
    group_name = " ".join(cmd_args)
    db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)
    count = db_group.get_all_sessions_count()
    for n in range(0, count, 10):
        sessions = db_group.get_all_sessions(n, 10)
        for session in sessions:
            print_session(session)


def get_file(context, cmd_args):
    assert len(cmd_args) == 1, "Wrong argument count."
    file_id = int(cmd_args[0])
    local_path = context.db.get_file_to_local(file_id)
    print("Got file ID %u at %s" % (file_id, local_path))


def dev_status(context, cmd_args):
    assert len(cmd_args) == 1, "Wrong argument count."
    timestamp = int(cmd_args[0])
    from dt_db_base import db_base_dev
    r = db_base_dev.get_dev_status_since(context.db, timestamp)
    for dev_uuid in r:
        dev = context.db.get_dev(dev_uuid)
        results = r[dev_uuid]
        for group in results:
            result = results[group]
            dev_id = dev.serial_number if dev else dev_uuid
            print('%s : "%s" : %s' % (dev_id.encode('ascii',errors='ignore'),
                group, "passed" if result[1] else "FAILED"))


def add_fail(context, cmd_args):
    assert len(cmd_args) >= 2, "Wrong argument count."
    uid = cmd_args[0]
    group_name = " ".join(cmd_args[1:])
    db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)

    tests = db_group.get_tests()

    results = {uid : {'tests': {tests[0].name : {'passfail' : False } } } }

    db_group.add_tests_results(results, tests)


def dev_results(context, cmd_args):
    assert len(cmd_args) == 1, "Wrong argument count."
    dev_uuid = cmd_args[0]
    dev = context.db.get_dev(dev_uuid)
    if not dev:
        print("Failed to find dev '%s'" % dev_uuid)
        sys.exit(-1)

    count = dev.get_session_count()

    for n in range(0, count, 10):
        sessions = dev.get_sessions(n, 10)
        for session in sessions:
            print_session(session)


def show_group(context, cmd_args):
    group_id = int(cmd_args[0])
    group = context.db.get_group_by_id(group_id)
    print("Group ID :", group_id)
    print("Group Name :", group.name)
    print("Group Desc :", group.desc)
    print("Group Note :", group.note)
    tests = group.get_tests()
    for test in tests:
        print("Test :", test.name)
        test.load_properties()
        for key, value in test.pending_properties.items():
            print("Arg:",key, "value(%s):" % (str(type(value))), value)


generic_cmds = {
    "update_tests" : (update_tests, "Update <groups yaml> in database."),
    "list_groups"  : (list_groups,  "List active groups."),
    "group_results": (group_results,"Get results for a <named> group."),
    "group_result" : (group_result, "Get result of a <named> group of <index>"),
    "group_dump"   : (group_dump,   "Get all results of <named> group (WARNING >all<)"),
    "get_file"     : (get_file,     "Get a file by id."),
    "dev_status"   : (dev_status,   "Get status of devices after given unix time."),
    "add_fail"     : (add_fail,     "Get <device> a fail for <named> group."),
    "dev_results"  : (dev_results,  "Get <device> results."),
    "show_group"   : (show_group,   "Print information about a <test group ID>"),
    }


def print_cmd_help(cmds):
    print("Commands:")
    for cmd, entry in cmds.items():
        print("%s : %s" % ("%14s" % cmd, "%14s" % entry[1]))


def execute_cmd(context, cmd, cmd_args, cmds):

    entry = cmds.get(cmd, None)

    if not entry:
        print("Unknown command : %s" % cmd)
        print_cmd_help(cmds)
    else:
        entry[0](context, cmd_args)
