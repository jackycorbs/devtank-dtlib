from __future__ import print_function, absolute_import

from collections import namedtuple
import hashlib
import copy
import time
import yaml
import sys
import os

from .db_process import test_group_t, group_entry_t, test_t, arg_t, db_process_t, obj_valid_at, as_human_time

import logging

def _db_str_or_null(s):
    return "'%s'" % s if s else "NULL"

def _db_int_or_null(db_id):
    return "%i" % db_id if db_id is not None else "NULL"


group_at_time_t = namedtuple('group_at_time', ['group', 'valid_from', 'valid_to'])


class merger_t(db_process_t):
    def __init__(self):
        self.old_c = None
        self.new_c = None
        self.old_machine_id_map = {}
        self.old_dev_id_map = {}
        self.old_file_id_map = {}
        self.file_dedupe = {}

        self.old_entry_id_map = {}

        self.old_groups_id_map = {}
        self.old_groups_name_map = {}
        self.old_tests_content_map = {}
        self.old_arg_content_map = {}
        self.old_tests_name_map = {}
        self.old_tests_id_map = {}
        self.old_session_id_map = {}
        self.old_result_id_map = {}

        self.importing_session_ids = []

        self.new_groups_id_map = {}
        self.new_groups_name_map = {}
        self.new_tests_content_map = {}
        self.new_arg_content_map = {}
        self.new_tests_name_map = {}
        self.new_tests_id_map = {}

        db_process_t.__init__(self)


    def copy_machines(self):
        print("Copy over machines")
        cmd = "SELECT id, hostname, mac FROM tester_machines"
        self.old_c.execute(cmd)
        rows = self.old_c.fetchall()
        for row in rows:
            org_machine_id, hostname, mac_address = row
            hostname = hostname.strip()
            mac_address = mac_address.strip()
            cmd = "SELECT id FROM tester_machines WHERE mac='%s'" % mac_address
            self.new_c.execute(cmd)
            r = self.new_c.fetchone()
            if r is None:
                cmd = "INSERT INTO tester_machines (hostname, mac) \
                    VALUES('%s', '%s')" % (hostname, mac_address)
                self.new_c.execute(cmd)
                new_machine_id = self.new_c.lastrowid
            else:
                new_machine_id = r[0]
            self.old_machine_id_map[org_machine_id] = new_machine_id

    def add_device(self, dev_row, dev_uid, dev_sn):
        return "INSERT INTO %s (uid, serial_number) \
            VALUES('%s', '%s')" % (self.dev_table, dev_uid, dev_sn)

    def copy_devices(self):
        print("Copy over devices")

        cmd = "SELECT id, uid, serial_number FROM %s" % self.dev_table
        self.old_c.execute(cmd)
        rows = self.old_c.fetchall()
        for row in rows:
            org_dev_id = row[0]
            dev_uid    = row[1]
            dev_sn     = row[2]

            cmd = "SELECT id FROM %s WHERE serial_number = '%s'" % (self.dev_table, dev_sn)
            self.new_c.execute(cmd)
            r = self.new_c.fetchone()
            if r is None:
                cmd = self.add_device(r, dev_uid, dev_sn)
                self.new_c.execute(cmd)
                new_dev_id = self.new_c.lastrowid
            else:
                new_dev_id = r[0]

            self.old_dev_id_map[org_dev_id] = new_dev_id

    def copy_files(self):
        print("Copy over files")

        self.file_dedupe = {}

        print("Hashing non-log files")
        # Select files not just results logs
        cmd = "SELECT files.id, files.filename, files.size FROM files WHERE files.id NOT IN (\
        SELECT files.id FROM files JOIN {results_table} \
        WHERE files.id = {results_table}.output_file_id OR \
        files.id = log_file_id)".format(results_table=self.results_table)
        self.new_c.execute(cmd)
        rows = self.new_c.fetchall()
        for row in rows:
            tupkey = self.get_file_key(self.new_c, *row)
            self.file_dedupe[tupkey] = row[0]

        # Select results logs
        print("Hashing log files")
        cmd = "SELECT files.id, files.filename, files.size  FROM files WHERE files.id IN (\
        SELECT files.id FROM files JOIN {results_table} \
        WHERE files.id = {results_table}.output_file_id OR \
        files.id = log_file_id)".format(results_table=self.results_table)
        self.new_c.execute(cmd)
        rows = self.new_c.fetchall()
        for row in rows:
            tupkey = self.get_file_key(self.new_c, *row, is_result=True)
            self.file_dedupe[tupkey] = row[0]

        self.old_file_id_map = {}

        folder = self.get_db_folder(self.new_c)
        cmd = "SELECT id, filename, size, modified_date, insert_time FROM files"
        self.old_c.execute(cmd)
        rows = self.old_c.fetchall()

        for row in rows:
            file_id = row[0]
            filepath = self.get_file(self.old_c, file_id)
            filesize = os.path.getsize(filepath)
            md5 = hashlib.md5(open(filepath,'rb').read()).hexdigest()
            tupkey = (row[1], row[2], md5)

            new_file_id = self.file_dedupe.get(tupkey, None)
            if new_file_id is None:
                file_store_id = self.get_rw_file_store(self.new_c)
                cmd = "INSERT INTO files (file_store_id, filename, size, \
    modified_date, insert_time) VALUES (%u, '%s', %u, %u, %u)" % (file_store_id,
                                                                  row[1], row[2],
                                                                  row[3], row[4])
                self.new_c.execute(cmd)
                new_file_id = self.new_c.lastrowid
                self.copy_file(folder, filepath, row[1], new_file_id)
                self.file_dedupe[tupkey] = new_file_id
            self.old_file_id_map[file_id] = new_file_id


    def get_result_row(self):
        return "%s.id, %s, group_entry_id, pass_fail, \
output_file_id, log_file_id, group_result_id, duration" % \
(self.results_table, self.results_table_dev)

    def add_result(self, row):
        # Remember that row[1:] of get_result_row
        row = list(row)
        row[0] = self.old_dev_id_map[row[0]]
        row[1] = self.old_entry_id_map[row[1]]
        #row[2] pass_fail
        row[3] = _db_int_or_null(self.old_file_id_map.get(row[3], None))
        row[4] = _db_int_or_null(self.old_file_id_map.get(row[4], None))
        row[5] = self.old_session_id_map[row[5]]
        row[6] = _db_int_or_null(row[6])
        return "INSERT INTO %s (%s, \
    group_entry_id, pass_fail, output_file_id, log_file_id, \
    group_result_id, duration) VALUES(%u, %u, %u, %s, %s, %u, %s)" \
    % tuple([self.results_table, self.results_table_dev] + row)

    def copy_results(self):
        print("Copy over Session Results")
        self.old_session_id_map = {}
        self.old_result_id_map = {}
        cmd = "SELECT test_group_results.id, test_groups.name, \
                      time_of_tests, test_groups.id, \
                      logs_tz_name, tester_machine_id, sw_git_sha1 \
            FROM test_group_results \
            JOIN test_groups ON test_groups.id = test_group_results.group_id"
        self.old_c.execute(cmd)
        rows = self.old_c.fetchall()

        old_results_map = {}
        for row in rows:
            session_id, name, timestamp, group_id, tz_name, machine_id, git_sha1 = row
            old_results_map[(name, timestamp)] = (session_id, group_id, tz_name, machine_id, git_sha1)

        # Result results at exactly the same time for a group named exacted the same.
        self.new_c.execute(cmd)
        rows = self.new_c.fetchall()
        for row in rows:
            old_session_id, name, timestamp, group_id, tz_name, machine_id, git_sha1 = row
            key = (name, timestamp)
            old_entry = old_results_map.pop(key, None)

        self.importing_session_ids = []

        for key in old_results_map:
            time_of_tests = key[1]
            old_session_id, old_group_id, tz_name, old_machine_id, git_sha1 = old_results_map[key]

            new_machine_id = self.old_machine_id_map.get(old_machine_id, None)

            group_id = self.get_match_group_at_time( self.old_groups_id_map[old_group_id], time_of_tests)
            cmd = "INSERT INTO test_group_results (group_id, time_of_tests, tester_machine_id, logs_tz_name, sw_git_sha1)\
     VALUES(%u, %u, %s, %s, %s)" % (group_id, time_of_tests,
                    _db_int_or_null(new_machine_id),
                    _db_str_or_null(tz_name),
                    _db_str_or_null(git_sha1))
            self.new_c.execute(cmd)
            new_session_id = self.new_c.lastrowid
            self.old_session_id_map[old_session_id] = new_session_id
            self.importing_session_ids += [old_session_id]

        print("Copy Results")

        cmd = "SELECT %s FROM %s JOIN test_group_results ON test_group_results.id = %s.group_result_id \
WHERE group_result_id in (%s)" % (self.get_result_row(),
                                  self.results_table,
                                  self.results_table,
                                  ",".join([str(session_id) for session_id in self.importing_session_ids]))
        c = self.old_c.execute(cmd)
        rows = self.old_c.fetchall()
        for row in rows:
            cmd = self.add_result(row[1:])
            self.new_c.execute(cmd)
            self.old_result_id_map[row[0]] = self.new_c.lastrowid

    def copy_results_values(self):
        cmd = 'SELECT id FROM "values" WHERE name = \'results_values\''
        c = self.new_c.execute(cmd)
        row = self.new_c.fetchone()
        result_values_parent = row[0]

        cmd = 'SELECT test_result_id,\
  "values".name,\
  value_text,\
  value_int,\
  value_real,\
  value_file_id,\
  valid_from, valid_to\
         FROM %s \
JOIN %s ON %s.id = test_result_id \
JOIN test_group_results ON test_group_results.id = %s.group_result_id \
JOIN "values" ON "values".id = value_id \
WHERE group_result_id in (%s)' % \
(self.results_values_table,
self.results_table, self.results_table, self.results_table,
",".join([str(session_id) for session_id in self.importing_session_ids]))
        c = self.old_c.execute(cmd)
        rows = self.old_c.fetchall()
        for row in rows:
            old_test_result_id = row[0]
            inserts = list(row[1:])
            file_id = inserts[4]
            if file_id:
                inserts[4] = self.get_remapped_file_id(None, file_id)

            inserts[0] = "'%s'" % inserts[0]
            if inserts[1]:
                inserts[1] = "'%s'" % inserts[1]

            inserts = [ "NULL" if i is None else i for i in inserts ]
            inserts.insert(5, result_values_parent)

            cmd = "INSERT INTO \"values\" \
        (name, value_text, value_int, value_real,\
        value_file_id, parent_id, valid_from, valid_to) VALUES \
        (%s, %s, %s, %s, %s, %s, %s, %s)" % tuple(inserts)
            self.new_c.execute(cmd)
            value_id = self.new_c.lastrowid

            cmd = "INSERT INTO %s (test_result_id, value_id) VALUES \
            (%u, %u)" % (self.results_values_table,
            self.old_result_id_map[old_test_result_id], value_id)
            self.new_c.execute(cmd)

    def get_group_state_at_time(self, group, current_time):
        entries = []
        bad_data = 0

        if not obj_valid_at(group, current_time):
            if current_time < group.valid_from:
                print("Warning, time request (%u) before group valid!" % current_time)
                group.valid_from = current_time
                bad_data = -1
            elif group.valid_to and current_time > group.valid_to:
                print("Warning, time request (%u) after group valid!" % current_time)
                group.valid_to = current_time + 1
                bad_data = 1
            else:
                print("Group %u not valid at time given %u." % (group.id, current_time))
                sys.exit(-1)

        if bad_data < 0:
            check_time = group.valid_from
        elif bad_data > 1:
            check_time = group.valid_to - 1
        else:
            check_time = current_time

        for entry in group.entries:
            if obj_valid_at(entry, check_time):
                if bad_data < 0:
                    entry.valid_from = current_time
                elif bad_data > 1:
                    entry.valid_to = current_time + 1
                args = []
                for arg in entry.args:
                    if obj_valid_at(arg, check_time):
                        if bad_data < 0:
                            arg.valid_from = current_time
                        elif bad_data > 1:
                            arg.valid_to = current_time + 1
                        args += [ arg ]
                d = entry._asdict()
                d['args'] = args
                entries += [ group_entry_t(**d) ]

        d = group._asdict()
        d['entries'] = entries
        return test_group_t(**d)

    def setup_maps(self, c):
        groups_id_map, groups_name_map = self.get_groups(c)

        tests_content_map = {}
        arg_content_map = {}

        for group in groups_id_map.values():
            for entry in group.entries:
                test_key = entry.test.name
                test_key_list = tests_content_map.get(test_key, [])
                test_key_list += [ entry.test ]
                tests_content_map[test_key] = test_key_list
                for arg in entry.args:
                    arg_key = self.make_key(arg)
                    arg_key_list = arg_content_map.get(arg_key, [])
                    arg_key_list += [ arg ]
                    arg_content_map[arg_key] = arg_key_list

        return groups_id_map, groups_name_map, tests_content_map, arg_content_map


    def get_in_timeslice(self, obj_list, timepoint):
        for obj in obj_list:
            if obj_valid_at(obj, timepoint):
                return obj

    def get_remapped_file_id(self, file_key, file_id):
        new_file_id = self.old_file_id_map.get(file_id, None)
        if  not new_file_id:
            new_file_id = self.file_dedupe.get(file_key, None) if file_key else None
            if not new_file_id:
                filepath = self.get_file(self.old_c, file_id)
                cmd = "SELECT filename, size, modified_date, insert_time FROM files WHERE id=%u" % file_id
                self.old_c.execute(cmd)
                row = self.old_c.fetchone()
                file_store_id = self.get_rw_file_store(self.new_c)
                cmd = "INSERT INTO files (file_store_id, filename, size, \
    modified_date, insert_time) VALUES (%u, '%s', %u, %u, %u)" % \
    (file_store_id, row)
                self.new_c.execute(cmd)
                new_file_id = self.new_c.lastrowid
                folder = self.get_db_folder(self.new_c)
                self.copy_file(folder, filepath, row[0], new_file_id)
                if file_key:
                    self.file_dedupe[file_key] = new_file_id
            file_id_map[file_id] = new_file_id
        return new_file_id

    def is_group_match_at_time(self, group_a, group_b, time_of_tests):

        old_entries = {}
        for entry in group_a.entries:
            if obj_valid_at(entry, time_of_tests):
                old_entries[entry.pos] = entry

        new_entries = {}
        for entry in group_b.entries:
            if obj_valid_at(entry, time_of_tests):
                new_entries[entry.pos] = entry

        if len(old_entries) != len(new_entries):
            self.debug_print(1, "WARNING : Not quite match.... different entry count.")
            return False

        for pos in old_entries:
            old_entry = old_entries[pos]
            new_entry = new_entries[pos]

            if old_entry.name != new_entry.name:
                self.debug_print(1, "WARNING : Not quite match.... different entry names.")
                return False

            if old_entry.test.file_key != new_entry.test.file_key:
                self.debug_print(1, "WARNING : Not quite match.... different test file.")
                return False

            if len(old_entry.args) != len(new_entry.args):
                self.debug_print(1, "WARNING : Not quite match.... different argument counts.")
                return False

        return old_entries, new_entries

    def get_mapped_match_group_at_time(self, group_at_time, time_of_tests):
        group_list = self.new_groups_name_map.get(group_at_time.name, None)
        if group_list:
            for new_group in group_list:
                if obj_valid_at(new_group, time_of_tests):

                    r = self.is_group_match_at_time(group_at_time, new_group, time_of_tests)
                    if not r:
                        continue

                    old_entries, new_entries = r

                    for pos in old_entries:
                        self.old_entry_id_map[old_entries[pos].id] = new_entries[pos].id

                    return new_group.id


    def get_match_group_at_time(self, group, time_of_tests):
        group_at_time = self.get_group_state_at_time(group, time_of_tests)

        new_group_id = self.get_mapped_match_group_at_time(group_at_time, time_of_tests)

        if new_group_id:
            return new_group_id

        new_groups = self.new_groups_name_map.get(group.name, None)
        if new_groups:
            if not group.valid_to:
                for new_group in new_groups:
                    if not new_group.valid_to and new_group.valid_from < group.valid_from:
                        cmd = "UPDATE \"test_groups\" SET valid_to=%u WHERE id=%u" % (group.valid_from, new_group.id)
                        self.new_c.execute(cmd)
                        for entry in new_group.entries:
                            if not entry.valid_to:
                                cmd = "UPDATE \"test_group_entries\" SET valid_to=%u WHERE id=%u" % (group.valid_from, entry.id)
                                self.new_c.execute(cmd)

        print("Creating new group of '%s'" % group.name)

        cmd = "INSERT INTO \"test_groups\" (name, description, creation_note, valid_from, valid_to) VALUES \
        ('%s','%s',%s, %u,%s)" % (group.name, group.desc, _db_str_or_null(group.notes),
            group.valid_from, _db_int_or_null(group.valid_to))
        self.new_c.execute(cmd)
        new_group_id = self.new_c.lastrowid

        new_entries = []

        folder = self.get_db_folder(self.new_c)

        for entry in group.entries:

            test = entry.test
            test_key = self.make_key(test)

            new_test = None
            new_tests = self.new_tests_content_map.get(test_key, None)
            if new_tests:
                new_test = self.get_in_timeslice(new_tests, entry.valid_from)
            if not new_test:
                new_file_id = self.get_remapped_file_id(test.file_key, test.file_id)
                cmd = "INSERT INTO \"tests\" (file_id, valid_from, valid_to) VALUES \
                (%u,%u,%s)" % (new_file_id, test.valid_from, _db_int_or_null(test.valid_to))
                self.new_c.execute(cmd)
                new_test_id = self.new_c.lastrowid
                new_test = test_t(new_test_id, test.name, test.file_key, new_file_id, test.valid_from, test.valid_to)
                if new_tests:
                    new_tests += [ new_test ]
                else:
                    new_tests = [ new_test ]
                self.new_tests_content_map[test_key] = new_tests

                self.new_tests_id_map[new_test.id] = new_test
                self.new_tests_name_map.setdefault(test.name, [])
                self.new_tests_name_map[test.name] += [ new_test ]

            cmd = "INSERT INTO \"test_group_entries\" \
    (name, test_group_id, test_id, valid_from, valid_to, order_position) \
    VALUES ('%s', %u, %u, %u ,%s, %u)" % (entry.name, new_group_id,
                                          new_test.id,  entry.valid_from,
                                          _db_int_or_null(entry.valid_to),
                                          entry.pos)
            self.new_c.execute(cmd)
            new_entry_id = self.new_c.lastrowid
            self.old_entry_id_map[entry.id] = new_entry_id

            entry_new_args = []
            for arg in entry.args:
                arg_key = self.make_key(arg)
                new_arg = None
                new_args = self.new_arg_content_map.get(arg_key, None)
                if new_args:
                    new_arg = self.get_in_timeslice(new_args, entry.valid_from)
                if not new_arg:
                    new_file_id = None
                    if arg.file_key:
                        new_file_id = self.get_remapped_file_id(arg.file_key, arg.file_id)

                    inserts = [arg.name, "'%s'" % arg.text if arg.text else None,
                               arg.int, arg.real, new_file_id, 4, arg.valid_from,
                               arg.valid_to ]
                    inserts = [ str(e) if e is not None else "NULL" for e in inserts ]

                    cmd = "INSERT INTO \"values\" \
                (name, value_text, value_int, value_real,\
                value_file_id, parent_id, valid_from, valid_to) VALUES \
                ('%s', %s, %s, %s, %s, %s, %s, %s)" % tuple(inserts)
                    self.new_c.execute(cmd)
                    new_arg_id = self.new_c.lastrowid
                    new_arg = arg_t(new_arg_id, arg.name, arg.text, arg.int, arg.real, arg.file_key, new_file_id, arg.valid_from, arg.valid_to)
                    if new_args:
                        new_args += [ new_arg ]
                    else:
                        new_args = [ new_arg ]
                    self.new_arg_content_map[arg_key] = new_args
                entry_new_args += [ new_arg ]

                cmd = "INSERT INTO \"test_group_entry_properties\" \
    (group_entry_id, value_id) VALUES(%u, %u)" % (new_entry_id,
                new_arg.id)
                self.new_c.execute(cmd)

            d = entry._asdict()
            d['args'] = entry_new_args
            d['test'] = new_test
            d['id'] = new_entry_id
            new_entry = group_entry_t(**d)
            new_entries += [ new_entry ]

        d = group._asdict()
        d['entries'] = new_entries
        d['id'] = new_group_id
        new_group = test_group_t(**d)
        self.new_groups_id_map[new_group.id] = new_group
        self.new_groups_name_map.setdefault(group_at_time.name, [])
        self.new_groups_name_map[group_at_time.name] += [new_group]
        new_group_id = self.get_mapped_match_group_at_time(group_at_time, time_of_tests)
        if not new_group_id:
            print("Should have should been created for old ID %u at time %u" % (group.id, time_of_tests))
            sys.exit(-1)
        return new_group_id

    def decuplicate_live_tests(self):
        for test_name in self.new_tests_name_map:
            tests_time_map = {}
            tests_list = self.new_tests_name_map[test_name]
            for test in tests_list:
                if not test.valid_to:
                    tests_time_map.setdefault(test.valid_from, [])
                    tests_time_map[test.valid_from] += [ test ]
            valid_froms = sorted(tests_time_map.keys())
            for n in range(0, len(valid_froms)):
                valid_from = valid_froms[n]
                tests_list = tests_time_map[valid_from]
                if n + 1 < len(valid_froms):
                    valid_to = valid_froms[n + 1]
                    for test in tests_list:
                        cmd = "UPDATE \"tests\" SET valid_to=%u WHERE id=%u" % (valid_to, test.id)
                        self.new_c.execute(cmd)

    def do_merge(self, old_db_url, new_db_url):
        print('Merging "%s" into "%s"' % (old_db_url, new_db_url))

        self.old_c = self.db_open(old_db_url)
        self.new_c = self.db_open(new_db_url)
        self.old_dev_id_map = {}
        self.old_file_id_map = {}
        self.file_dedupe = {}
        self.old_entry_id_map = {}

        cmd = 'SELECT value_int FROM "values" WHERE id=1'

        self.new_c.execute(cmd)
        new_db_version = self.new_c.fetchone()[0]
        self.old_c.execute(cmd)
        old_db_version = self.old_c.fetchone()[0]

        if new_db_version != 5 and new_db_version != 5:
            print("Unable to merge into v%u database." % new_db_version)
            return -1

        self.load_custom_table_names(self.new_c)

        self.new_tests_id_map, self.new_tests_name_map = self.get_tests(self.new_c)
        self.old_tests_id_map, self.old_tests_name_map = self.get_tests(self.old_c)

        self.new_groups_id_map, self.new_groups_name_map, \
            self.new_tests_content_map, self.new_arg_content_map = self.setup_maps(self.new_c)
        self.old_groups_id_map, self.old_groups_name_map, \
            self.old_tests_content_map, self.old_arg_content_map = self.setup_maps(self.old_c)

        self.copy_machines()
        self.copy_devices()
        self.copy_files()
        self.copy_results()
        self.copy_results_values()
        self.decuplicate_live_tests()

        self.commit(self.new_c)
