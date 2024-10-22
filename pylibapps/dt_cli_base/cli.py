import os
import sys
import yaml
import hashlib
import dt_db_base
from datetime import datetime

def list_groups(context, cmd_args):
    groups = context.db.get_groups()
    longest_name = 0
    for group in groups:
        if len(group.name) > longest_name:
            longest_name = len(group.name)

    for group in groups:
        print('Group : %4s : "%*.s%s" - "%s"' % ("%u" % group.id, longest_name - len(group.name), "", group.name, group.desc))


def update_tests(context, cmd_args):
    assert len(cmd_args) == 1, "update_tests takes one argument, the path to the yaml file containing the groups."

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
    assert len(cmd_args) > 0, "group_results takes one argument, the group name."
    group_name = " ".join(cmd_args)
    if group_name.isnumeric():
        group_name = int(group_name)
        db_group = context.db.get_group_by_id(group_name)
    else:
        db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)
    if isinstance(group_name, int):
        count = db_group.get_sessions_count()
    else:
        count = db_group.get_all_sessions_count()
    print("Group has %u result sessions." % count)


def print_session(session):
    print("=" * 72)
    dt = datetime.fromtimestamp(session.time_of_tests)
    print("Time :", dt.isoformat(sep=" "), dt.astimezone().tzname())
    print("Overall :", "passed" if session.pass_fail else "FAILED")
    print("Session :", session.id)
    machine = session.get_tester_line_str()
    if machine:
        print("Tester :", machine)
    for dev_uuid, dev_results in session.devices.items():
        dev = session.db.get_dev(dev_uuid)
        if dev_uuid != dev.serial_number:
            print("Device : %s, %s" % (dev_uuid, dev.serial_number))
        else:
            print("Device : ", dev_uuid)

        for result in dev_results.results:
            if len(result):
                print('Test : "%s" (Output File:%s, Log File:%s) - %s (%Gs)' % (
                        result[1],
                        "%u" % result[2] if result[2] else "NONE",
                        "%u" % result[3] if result[3] else "NONE",
                        "passed" if result[0] else "FAILED",
                        dt_db_base.db_time(result[-2]) if result[-2] is not None else 0 ))


def group_result(context, cmd_args):
    assert len(cmd_args) > 0, "group_result takes two arguments, the group name, followed by the session index."
    group_name = " ".join(cmd_args[:-1])
    if group_name.isnumeric():
        group_name = int(group_name)
        db_group = context.db.get_group_by_id(group_name)
    else:
        db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)
    session_index = int(cmd_args[-1])
    if isinstance(group_name, int):
        sessions = db_group.get_sessions(session_index, 1)
    else:
        sessions = db_group.get_all_sessions(session_index, 1)
    if not sessions:
        print("Result session not found of index %u" % session_index)
        sys.exit(-1)

    print_session(sessions[0])


def group_dump(context, cmd_args):
    assert len(cmd_args) > 0, "group_dump takes one argument, the group name."
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
    assert len(cmd_args) >= 1, "get_file takes one argument, the file_id (integer)"
    n = 0
    while n < len(cmd_args):
        file_id = int(cmd_args[n])
        local_path = context.db.get_file_to_local(file_id)
        print("Got file ID %u at %s" % (file_id, local_path))
        n += 1


def dev_status(context, cmd_args):
    assert len(cmd_args) == 1, "dev_status takes one argument, the db_timestamp (integer)"
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
    dev = cli_get_device(context.db, uid)
    uid = dev.uuid
    group_name = " ".join(cmd_args[1:])
    db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)

    tests = db_group.get_tests()

    results = {uid : {'tests': {tests[0].name : {'passfail' : False } } } }

    db_group.add_tests_results([dev], results, tests)


def add_pass(context, cmd_args):
    assert len(cmd_args) >= 2, "Wrong argument count."
    uid = cmd_args[0]
    dev = cli_get_device(context.db, uid)
    uid = dev.uuid
    group_name = " ".join(cmd_args[1:])
    db_group = context.db.get_group(group_name)
    if not db_group:
        print('No group of name "%s" found.' % group_name)
        sys.exit(-1)

    tests = db_group.get_tests()

    results = {uid : {'tests': dict([(test.name, {'passfail' : True}) for test in tests]) } }

    db_group.add_tests_results([dev], results, tests)



def dev_results(context, cmd_args):
    assert len(cmd_args) >= 1, "dev_results takes one argument, the device's uuid."
    dev_uuid = cmd_args[0]
    dev = cli_get_device(context.db, dev_uuid)
    step = 10
    if len(cmd_args) > 1:
        count = int(cmd_args[1])
        if count < step:
            step = 1
    else:
        count = dev.get_session_count()

    for n in range(0, count, step):
        sessions = dev.get_sessions(n, step)
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
        print("Test File :", test.get_file_to_local())
        test.load_properties()
        for key, value in test.pending_properties.items():
            print("Arg:",key, "value(%s):" % (str(type(value))), value)



_ANSI_RED     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_WARN    = "\x1B[33m"
_ANSI_DEFAULT = "\x1B[39m"


def print_line(colorcode, msg):
    sys.stdout.write(colorcode + msg + _ANSI_DEFAULT)

_debug_messages = False



def run_group(context, cmd_args, submit=True):
    import gi
    gi.require_version('GLib', '2.0')
    from gi.repository import GLib

    assert len(cmd_args) > 1, "run_group takes twos argument, the group name and device serial"
    group_name = " ".join(cmd_args[0:-1])
    db_dev = cli_get_device(context.db, cmd_args[-1])

    context.devices = [db_dev]

    db_group = context.db.get_group(group_name)
    if not db_group:
        print('Failed to find tests group "%s"' % group_name)
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
    if submit:
        run_group_man.submit()
    if not run_group_man.is_pass:
        sys.exit(-1)


def dry_run_group(context, cmd_args):
    run_group(context, cmd_args, False)


def _get_group_hash(group, print_tests_hash, longest_name=0):
    hash_md5 = hashlib.md5()
    tests = group.get_tests()
    for test in tests:
        test_hash_md5 = hashlib.md5()
        test_hash_md5.update(test.name.encode())
        filepath = test.get_file_to_local()
        test_hash_md5.update(open(filepath, "rb").read())
        test.load_properties()
        for key, value in test.pending_properties.items():
            test_hash_md5.update(key.encode())
            if isinstance(value, str):
                if os.path.exists(value):
                    test_hash_md5.update(open(value, "rb").read())
                else:
                    test_hash_md5.update(value.encode())
            else:
                test_hash_md5.update(str(value).encode())
        test_hash = test_hash_md5.hexdigest()
        if print_tests_hash:
            print(test_hash,  "%s%*.s" % (group.name, longest_name - len(group.name), ""), test.name)
        hash_md5.update(test_hash.encode())
    return hash_md5.hexdigest()



def groups_hash(context, cmd_args):
    print_tests_hash = True if len(cmd_args) > 0 else False
    groups = context.db.get_groups()
    longest_name = 0
    for group in groups:
        if len(group.name) > longest_name:
            longest_name = len(group.name)

    for group in groups:
        print('Group : %4s : "%*.s%s" - "%s"' % ("%u" % group.id, longest_name - len(group.name), "", group.name, group.desc))
        print("MD5:", _get_group_hash(group, print_tests_hash, longest_name))


def find_group_hash(context, cmd_args):
    target_hash = cmd_args[0]
    group_name = " ".join(cmd_args[1:])
    db_group = context.db.get_group(group_name)
    if not db_group:
        print('Failed to find tests group "%s"' % group_name)
        sys.exit(-1)

    versions = db_group.get_version_times()
    for ts, group_version in versions:
        group_hash = _get_group_hash(group_version, False)
        if group_hash == target_hash:
            print("FOUND at", datetime.fromtimestamp(dt_db_base.db2py_time(ts)))


def update_test(context, cmd_args):
    db = context.db

    test_script = cmd_args[0]
    test_filename = os.path.basename(test_script)

    def hash_test_file(filepath):
        test_hash_md5 = hashlib.md5()
        test_hash_md5.update(open(filepath, "rb").read())
        return test_hash_md5.hexdigest()

    test_script_hash = hash_test_file(test_script)

    now = dt_db_base.db_ms_now()
    tests = db.get_all_tests(now)
    to_replace = []
    matching = []
    for test in tests:
        if test.filename == test_filename:
            local_file = test.get_file_to_local()
            test_hash = hash_test_file(local_file)
            if test_script_hash != test_hash:
                to_replace += [test]
            else:
                matching += [test]

    c = db.db.cursor()

    if len(to_replace) or not len(matching):
        while len(to_replace):
            test = to_replace.pop()
            test.remove(c, now)

        new_test_obj = db.add_test(test_script, db_cursor=c, now=now)
        matching += [new_test_obj]

    if len(matching) > 1:
        print("Multiple instances of test of same name.")

    new_test_obj = matching[0]

    groups = context.db.get_groups(now)
    for group in groups:
        tests = group.get_tests(now)
        to_replace = []
        pos = 0
        for test in tests:
            if test.filename == test_filename:
                local_file = test.get_file_to_local()
                test_hash = hash_test_file(local_file)
                if test_script_hash != test_hash:
                    to_replace += [(test, pos)]
            pos += 1
        while len(to_replace):
            test, pos = to_replace.pop()
            group.remove_test(test, c, now)
            group.add_test(new_test_obj, c, pos, now)

    db.db.commit()

def add_tar_filestore(context, cmd_args):
    db = context.db
    tt = dt_db_base.tar_transferer
    db.add_filestore(tt.server_name, "", 0, tt.protocol_id)
    db.add_filestore_protocol(tt.protocol_name)
    vfs_row = db.get_tar_virtual_filestore()
    if not vfs_row:
        raise Exception("Empty response from get_tar_virtual_filestore()")
    if vfs_row[1] != tt.protocol_id:
        raise Exception(f"Tar protocol ID not equal to {tt.protocol_id}!")
    print("Virtual filestore feature added successfully.")

def export_csv(context, cmd_args):
    nargs = len(cmd_args)
    if nargs < 1:
        print_cmd_help()
        return
    filename = cmd_args[0]
    before = None
    after = None
    if nargs > 1:
        to_micro = lambda t: \
        int(datetime.fromisoformat(t).timestamp()) * 1000000
        try:
            before = to_micro(cmd_args[1])
            if nargs > 2:
                after = to_micro(cmd_args[2])
        except ValueError as e:
            print(f"Error parsing timestamp: {e}")
            return
    context.db.generate_csv(filename, before, after)


def grep_files(context, cmd_args):
    assert len(cmd_args) > 1, "Wrong argument count."

    needle = cmd_args[0]

    n = 1
    while n < len(cmd_args):
        file_id = int(cmd_args[n])
        local_path = context.db.get_file_to_local(file_id)
        os.system(f'grep -H "{needle}" "{local_path}"')
        n += 1


def list_testers(context, cmd_args):
    machines = dt_db_base.db_tester_machine.get_all_machines(context.db)
    for machine in machines:
        print(f"{machine.id} : {machine.mac} {machine.hostname}")


def testers_results(context, cmd_args):
    tester_id = int(cmd_args[0])
    machine = dt_db_base.db_tester_machine.get_by_id(context.db, tester_id)
    if machine:
        print(f"Machine {tester_id} has {machine.get_sessions_count()} result sessions.")
    else:
        print(f"Machine {tester_id} not found.")


def testers_result(context, cmd_args):
    tester_id = int(cmd_args[0])
    offset = int(cmd_args[1])
    machine = dt_db_base.db_tester_machine.get_by_id(context.db, tester_id)
    if machine:
        sessions = machine.get_sessions(offset, 10)
        for session in sessions:
            print_session(session)
    else:
        print(f"Machine {tester_id} not found.")


generic_cmds = {
    "update_tests"      : (update_tests,      "Update <groups yaml> in database."),
    "list_groups"       : (list_groups,       "List active groups."),
    "group_results"     : (group_results,     "Get results for a <named/id> group."),
    "group_result"      : (group_result,      "Get result of a <named/id> group of <index>"),
    "group_dump"        : (group_dump,        "Get all results of <named> group (WARNING >all<)"),
    "get_file"          : (get_file,          "Get a file by <id>."),
    "dev_status"        : (dev_status,        "Get status of devices after given <unix time>."),
    "add_fail"          : (add_fail,          "For <device> add a fake fail for <named> group."),
    "add_pass"          : (add_pass,          "For <device> add a fake pass for <named> group."),
    "dev_results"       : (dev_results,       "Get <device> results."),
    "show_group"        : (show_group,        "Print information about a <test group ID>"),
    "dry_run_group"     : (dry_run_group,     "Dry run (no DB commit) group <name> on attached <device>."),
    "run_group"         : (run_group,         "Run group <name> on attached <device>."),
    "groups_hash"       : (groups_hash,       "Generate hashes for each group (<show tests>)"),
    "find_group_hash"   : (find_group_hash,   "Take given <hash> and <name> and search if in given database."),
    "update_test"       : (update_test,       "Update given test script used in any test groups."),
    "add_tar_filestore" : (add_tar_filestore, "Enable the tar virtual filestore feature in the database."),
    "export_csv"        : (export_csv,        "export_csv <filename> [before] [after] : Export a CSV dump of database results in <filename>. Optional dates take the format YYYY-MM-DD:HH:MM:SS"),
    "grep_files"        : (grep_files,        "Grep for given text in given files."),
    "list_testers"      : (list_testers,      "List all testers."),
    "testers_results"   : (testers_results,   "Count session count of <tester ID>."),
    "testers_result"    : (testers_result,    "Get sessions of <tester ID> from <offset>."),
}


def print_cmd_help(cmds):
    print("Commands:")
    for cmd, entry in cmds.items():
        print("%s : %s" % ("%14s" % cmd, "%14s" % entry[1]))


def cli_get_device(db, dev_str):
    db_dev = db.get_dev(dev_str)
    if not db_dev:
        db_dev = db.get_dev_by_sn(dev_str)
        if not db_dev:
            print("Not found device :", dev_str)
            sys.exit(-1)
    return db_dev


def execute_cmd(context, cmd, cmd_args, cmds):

    if context.args['verbose'] or os.environ.get("DEBUG", ""):
        global _debug_messages
        dt_db_base.enable_info_msgs(True)
        _debug_messages = True

    entry = cmds.get(cmd, None)

    if not entry:
        print("Unknown command : %s" % cmd)
        print_cmd_help(cmds)
    else:
        entry[0](context, cmd_args)
