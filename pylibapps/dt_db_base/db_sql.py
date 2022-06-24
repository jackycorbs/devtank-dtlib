from __future__ import print_function, absolute_import

import datetime
from dateutil.tz import tzlocal
import time
import sys


from .db_common import *
from .c_base import dt_get_build_info


_id_null = lambda x: ("%i" % x) if x else "NULL"
_int_null = lambda x: ("%i" % x) if x is not None else "NULL"


class sql_common(object):

    def __init__(self):
        self.dev_result_table_name = "dev_result_table"
        self.dev_result_values_table_name = None
        self.devices_table_name = "devs"
        self.device_key_name = "dev_id"
        self.db_version = None

        self.defaults_id = 3
        self.settings_id = 2
        self.test_props_id = 4
        self.result_props_id = None

    def setup(self, db):
        cmd = self.get_dynamic_table_info()
        row = db.query_one(cmd)
        assert row, "Nothing returned for dynamic table names."
        self.use_dynamic_table_info(row)
        rows = db.query(self.get_result_values_parent_id())
        if rows:
            assert len(rows) == 1, "Should be one entry for results values parent."
            self.result_props_id = rows[0][0]
    """
    ====================================================================

     Device related SQL

    """
    def get_update_dev_uid(self, dev_id, new_uuid):
        return "\
UPDATE %s SET uid='%s' WHERE id=%i" % \
(self.devices_table_name, db_safe_str(new_uuid), dev_id)

    def get_dev_by_serial(self, serial_number):
        return "SELECT serial_number, id, uid FROM %s WHERE \
serial_number='%s'" % (self.devices_table_name,
                        db_safe_str(serial_number))

    def get_dev_by_uid(self, uuid):
        return "SELECT serial_number, id, uid FROM %s WHERE \
uid='%s'" % (self.devices_table_name, db_safe_str(uuid))

    def get_dev_by_id(self, dev_id):
        return "SELECT serial_number, id, uid FROM %s WHERE \
id=%i" % (self.devices_table_name, dev_id)

    def get_dev_status_since(self, timestamp):
        return "\
SELECT {0}.uid, test_groups.name, MAX(test_group_results.time_of_tests), MIN(pass_fail) FROM test_group_results \
JOIN test_groups ON test_groups.id = test_group_results.group_id \
JOIN {1} ON {1}.group_result_id = test_group_results.id \
JOIN {0} ON {0}.id = {1}.{3} \
WHERE time_of_tests > {2} GROUP BY {0}.id, test_groups.name\
".format(self.devices_table_name,
         self.dev_result_table_name,
         timestamp,
         self.device_key_name)

    def get_dev_session_count(self, dev_id):
        return "\
SELECT COUNT(DISTINCT test_group_results.id) \
    FROM %s \
JOIN test_group_results ON test_group_results.id = group_result_id \
WHERE %s.%s=%u" % (self.dev_result_table_name,
                   self.dev_result_table_name,
                   self.device_key_name,
                   dev_id)

    def get_dev_sessions(self, dev_id, offset, count):
        return "\
SELECT DISTINCT test_group_results.id, \
      test_group_results.time_of_tests, \
      test_group_results.group_id, \
      mac, hostname \
FROM %s \
JOIN test_group_results ON test_group_results.id = group_result_id \
LEFT JOIN tester_machines ON tester_machines.id = tester_machine_id \
WHERE %s.%s=%u ORDER BY test_group_results.time_of_tests DESC LIMIT %u OFFSET %u" \
% (self.dev_result_table_name,
   self.dev_result_table_name,
   self.device_key_name,
   dev_id, count, offset)


    def get_dev_last_result(self, dev_id, group_name):
        return "SELECT test_group_results.time_of_tests, MIN(%s.pass_fail) FROM %s \
JOIN test_group_results on test_group_results.id = %s.group_result_id \
JOIN test_groups ON test_groups.id = test_group_results.group_id \
WHERE %s.%s = %u AND test_groups.name = '%s' \
GROUP BY test_group_results.time_of_tests \
ORDER BY test_group_results.time_of_tests DESC LIMIT 1" \
% (self.dev_result_table_name,
   self.dev_result_table_name,
   self.dev_result_table_name,
   self.dev_result_table_name,
   self.device_key_name, dev_id, db_safe_str(group_name))

    """
    ====================================================================

     File related SQL

    """
    def get_file_store_protocol_id(self, protocol_name):
        return "SELECT id FROM file_store_protocols WHERE name='%s'"\
 % db_safe_str(protocol_name)

    def add_file_store(self, server_name, server_folder, is_writable,
                       protocol_id):
        return "INSERT INTO file_stores \
(server_name, base_folder, is_writable, protocol_id) \
VALUES('%s', '%s', %i, %i)" % \
(db_safe_str(server_name), db_safe_str(server_folder), is_writable, \
protocol_id)

    def update_file_store_writable(self, filestore_id, is_writable):
        return "UPDATE file_stores SET is_writable \
WHERE is_writable=%i AND id=%i" % (is_writable, filestore_id)

    def get_file_filestore(self, file_id):
        return "SELECT server_name, protocol_id, base_folder, \
filename, modified_date, size FROM files \
JOIN file_stores ON file_store_id=file_stores.id \
WHERE files.id=%i" % file_id

    def get_all_file_stores(self):
        return "SELECT id, server_name, base_folder, protocol_id, \
is_writable FROM file_stores"

    def get_rw_file_store(self):
        return "SELECT id, server_name, base_folder, protocol_id FROM \
file_stores WHERE is_writable=1 LIMIT 1"

    def get_resource_files(self):
        dev_result_table_name = self.dev_result_table_name
        return "\
SELECT files.id, files.filename FROM files \
JOIN \"values\" ON value_file_id = files.id"

    def get_file_by_name(self, name):
        return "\
SELECT files.id FROM files WHERE files.filename='%s'" % name

    def add_file(self, filename, filestore_id, now, mod_time, size):
        return "\
INSERT INTO files \
(filename, file_store_id, insert_time, modified_date, size) \
VALUES('%s', %i, %i, %i, %i)" % \
(db_safe_str(filename), filestore_id, now, mod_time, size)

    def get_filename(self, file_id):
        return "SELECT filename FROM files WHERE files.id=%i" % file_id

    def link_tar_file(self, tar_file_id, file_id):
        return "\
INSERT INTO tar_files \
(parent_file_id, file_id) VALUES(%u, %u)" % (tar_file_id, file_id)

    def complete_tar_file(self, tar_file_id, modtime, filesize):
        return "\
UPDATE files SET modified_date=%i, size=%u WHERE id=%u" % (modtime, filesize, tar_file_id)

    def get_tar_id(self, file_id):
        return "SELECT parent_file_id FROM tar_files WHERE file_id=%u" % file_id

    def get_tar_virtual_filestore(self):
        return "SELECT id FROM file_stores WHERE server_name = 'virtual_tars'"

    """
    ====================================================================

     Test related SQL

    """
    def add_test(self, file_id, valid_from):
        return "INSERT INTO tests (file_id, valid_from) VALUES(%i, %i)"\
         % (file_id, valid_from)

    def get_all_tests(self, now):
        return "\
SELECT tests.id, files.filename, tests.file_id FROM tests \
JOIN files ON tests.file_id=files.id \
WHERE tests.valid_from<=%i AND \
(tests.valid_to IS NULL OR tests.valid_to>%i)" % (now, now)

    def get_test_by_id(self, test_id):
        return "\
SELECT tests.id, files.filename, tests.file_id FROM tests \
JOIN files ON tests.file_id=files.id \
WHERE tests.id=%i" % (test_id)

    def get_test_by_name(self, name, now):
        return "\
SELECT tests.id, files.filename, tests.file_id FROM tests \
JOIN files ON tests.file_id=files.id \
WHERE files.filename='%s' AND \
tests.valid_from<=%i AND (tests.valid_to IS NULL OR tests.valid_to>%i)"\
% (db_safe_str(name), now, now)

    def get_deleted_tests(self, now):
        return "\
SELECT tests.id, files.filename, tests.file_id FROM tests \
JOIN files ON tests.file_id=files.id \
WHERE tests.id IN ( \
SELECT MAX(tests.id) FROM tests \
WHERE \
tests.valid_from<=%i AND tests.valid_to<=%i \
AND tests.file_id NOT IN (\
SELECT tests.file_id FROM tests \
JOIN files ON tests.file_id=files.id \
WHERE tests.valid_from<=%i AND \
(tests.valid_to IS NULL OR tests.valid_to>%i)\
) GROUP BY file_id )" % (now, now, now, now)

    def remove_test(self, test_id, now):
        return "\
UPDATE tests SET valid_to=%i WHERE id=%i" % (now, test_id)

    def get_tests(self, group_id, now):
        dev_result_table_name = self.dev_result_table_name
        return "\
SELECT tests.id, filename, file_id, test_group_entries.name, \
       test_group_entries.id AS entry_id, order_position, \
       (SELECT MAX(duration) FROM %s \
          WHERE group_entry_id=test_group_entries.id \
                AND pass_fail=1) AS duration \
FROM tests \
JOIN files ON tests.file_id=files.id \
JOIN test_group_entries ON test_group_entries.Test_id=tests.id \
WHERE (test_group_entries.valid_to IS NULL OR \
test_group_entries.valid_to>%i) AND \
test_group_entries.valid_from<=%i AND \
test_group_entries.test_group_id=%i \
ORDER BY order_position" % (dev_result_table_name, now, now, group_id)

    """
    ====================================================================

     tests group related SQL

    """
    def add_test_group(self, name, desc, valid_from, note=None):
        return "\
INSERT INTO test_groups (name, description, creation_note, valid_from) \
VALUES('%s', '%s', %s, %i)" % (db_safe_str(name), db_safe_str(desc),
db_safe_null_str(note), valid_from)

    def add_test_group_test(self, group_id, test_id, name, order_pos,
                            valid_from):
        return "\
INSERT INTO test_group_entries (test_group_id, Test_id, name, \
                                order_position, valid_from) \
VALUES(%i, %i, '%s', %i, %i)" % \
(group_id, test_id, db_safe_str(name), order_pos, valid_from)

    def add_test_group_value(self, group_entry_id, value_id):
        return "\
INSERT INTO test_group_entry_properties (group_entry_id, Value_id) \
VALUES(%i, %i)" % (group_entry_id, value_id)

    def remove_test_group_tests(self, group_entry_id, now):
        return "\
UPDATE test_group_entries SET valid_to=%i WHERE id=%i" % \
(now, group_entry_id)

    _GROUP_SQL="SELECT id, name, description FROM test_groups "

    def get_groups(self, now):
        return self._GROUP_SQL + "\
WHERE valid_from<=%i AND (valid_to IS NULL OR valid_to>%i)" % \
(now, now)

    def get_group_by_name(self, name, now):
        return self._GROUP_SQL + "\
WHERE valid_from<=%i AND (valid_to IS NULL OR valid_to>%i) \
AND name='%s'" % (now, now, db_safe_str(name))

    def get_group_by_id(self, group_id):
        return self._GROUP_SQL + " WHERE id=%i" % group_id

    def get_group_name_versions(self, name):
        return "SELECT * FROM ( \
SELECT test_groups.id, test_groups.valid_from FROM test_groups \
JOIN test_group_entries ON test_group_entries.test_group_id = test_groups.id \
WHERE test_groups.name='{0}' \
UNION \
SELECT test_groups.id, test_group_entries.valid_from FROM test_groups \
JOIN test_group_entries ON test_group_entries.test_group_id = test_groups.id \
WHERE test_groups.name='{0}' \
) AS temp \
GROUP BY id, valid_from \
ORDER BY valid_from".format(db_safe_str(name))

    def remove_test_group(self, group_id, now):
        return "\
UPDATE test_groups SET valid_to=%i WHERE id=%i" % (now, group_id)

    def set_test_group_name(self, group_id, name):
        return "\
UPDATE test_groups SET name='%s' WHERE id=%i" % (db_safe_str(name),\
                                                 group_id)

    def set_test_group_desc(self, group_id, desc):
        return "\
UPDATE test_groups SET description='%s' WHERE id=%i" % \
(db_safe_str(desc), group_id)

    def get_test_group_durations(self, group_id, now):
        dev_result_table_name = self.dev_result_table_name
        return "\
SELECT test_group_entries.id, MAX(%s.duration) FROM test_group_entries \
JOIN %s ON %s.group_entry_id=test_group_entries.id \
WHERE test_group_id=%i AND valid_from<=%i AND \
(valid_to IS NULL OR valid_to>%i) GROUP BY test_group_entries.id" % (
dev_result_table_name, dev_result_table_name, dev_result_table_name,
group_id, now, now)

    def get_test_group_creation_note(self, group_id):
        return "SELECT creation_note FROM test_groups WHERE id=%u" % group_id

    """
    ====================================================================

     results related SQL

    """
    def add_test_group_results(self, group_id, machine_id, now):
        if self.db_version > 3:
            tz = tzlocal()
            tz_name = tz.tzname(datetime.datetime.now(tz))
            sw_git_sha1 = dt_get_build_info()[1][:7]
            return "\
    INSERT INTO test_group_results \
        (group_id, time_Of_tests, logs_tz_name, \
         tester_machine_id, sw_git_sha1) \
    VALUES (%i, %i, '%s', %s, '%s')" % (
            group_id, now, db_safe_str(tz_name),
            _id_null(machine_id), db_safe_str(sw_git_sha1))
        else:
            return "\
    INSERT INTO test_group_results (group_id, Time_Of_tests) \
    VALUES (%i, %i)" % (group_id, now)

    def get_test_group_results_count(self, group_id):
        return "\
SELECT COUNT(id) FROM test_group_results WHERE group_id=%i" % \
group_id

    def get_test_group_results_count_by_name(self, group_name):
        return "\
SELECT COUNT(test_group_results.id) FROM test_group_results \
JOIN test_groups ON test_groups.id = test_group_results.group_id \
WHERE test_groups.name='%s'" % \
db_safe_str(group_name)

    def get_test_group_results(self, group_id, offset, count):
        return "\
SELECT test_group_results.id, Time_Of_tests, mac, hostname \
FROM test_group_results \
LEFT JOIN tester_machines ON tester_machines.id = test_group_results.tester_machine_id \
WHERE group_id=%i \
ORDER BY Time_Of_tests DESC LIMIT %u OFFSET %u" % (group_id, count, offset)

    def get_test_group_results_by_name(self, group_name, offset, count):
        return "\
SELECT test_group_results.id, Time_Of_tests, group_id, mac, hostname \
FROM test_group_results \
JOIN test_groups ON test_groups.id = test_group_results.group_id \
LEFT JOIN tester_machines ON tester_machines.id = test_group_results.tester_machine_id \
WHERE test_groups.name='%s' \
ORDER BY Time_Of_tests DESC LIMIT %u OFFSET %u" % (db_safe_str(group_name), count, offset)

    def get_sessions(self, session_ids):
        return "\
SELECT test_group_results.id, Time_Of_tests, \
    group_id, name, description, mac, hostname \
FROM test_group_results JOIN test_groups ON test_groups.id = group_id \
LEFT JOIN tester_machines ON tester_machines.id = test_group_results.tester_machine_id \
WHERE test_group_results.id IN (%s) ORDER BY Time_Of_tests DESC" % \
",".join([str(session_id) for session_id in session_ids])

    def get_dev_results(self, session_id):
        return "\
SELECT {results}.id, {devs}.uid, pass_fail, output_file_id, \
      log_file_id, Test_id, name, filename, order_position, \
      {devs}.serial_number \
FROM {results} \
JOIN test_group_entries ON \
    test_group_entries.id = {results}.group_entry_id \
JOIN tests ON tests.id = test_group_entries.Test_id \
JOIN files ON files.id = tests.file_id \
JOIN {devs} ON {devs}.id = {results}.{dev_key} \
WHERE {results}.group_result_id={session_id}".format(
results=self.dev_result_table_name,
devs=self.devices_table_name,
dev_key=self.device_key_name,
session_id=session_id)

    def get_test_group_results_tests(self, session_id, now):
        return "\
SELECT test_group_entries.order_position, test_group_entries.name,\
       files.filename, test_group_entries.id AS group_entry_id \
FROM test_group_results \
JOIN test_groups ON test_groups.id = group_id \
JOIN test_group_entries ON test_group_entries.test_group_id = group_id \
JOIN tests ON tests.id = test_group_entries.Test_id \
JOIN files ON files.id = tests.file_id \
WHERE test_group_results.id=%i AND \
test_group_entries.valid_from<=%i AND \
(test_group_entries.valid_to IS NULL OR test_group_entries.valid_to>%i)\
 ORDER BY test_group_entries.order_position" % (session_id, now, now)

    def add_dev_result(self, session_id, dev_id, group_entry_id,
                       pass_fail, output_file_id, log_file_id,
                       duration):
        dev_result_table_name = self.dev_result_table_name
        device_key_name = self.device_key_name
        return "\
INSERT INTO %s \
(group_result_id, %s, group_entry_id, pass_fail, output_file_id,\
log_file_id, duration) \
VALUES (%i, %i, %i, %i, %s, %s, %s)" % \
 (dev_result_table_name, device_key_name, session_id, dev_id,
  group_entry_id, int(pass_fail), _id_null(output_file_id),\
  _id_null(log_file_id), _int_null(duration))

    def add_test_value(self, result_id, value_id):
        dev_result_values_table_name = \
        self.dev_result_values_table_name
        if not dev_result_values_table_name:
            return None
        return "\
INSERT INTO %s (test_result_id, value_id) VALUES (%i, %i)" % \
(dev_result_values_table_name, result_id, value_id)
    """
    ====================================================================

     Values related SQL

    """

    def get_version(self):
        return "SELECT name, value_int FROM \"values\" WHERE id=1"

    def add_default_value(self, name, valid_from):
        return "\
INSERT INTO \"values\" (name, parent_id, valid_from) \
VALUES('%s', %i, %i)" % \
(db_safe_str(name), self.defaults_id, valid_from)

    def add_default_value_str_param(self, name, parent_id, value,
                                    valid_from):
        return "\
INSERT INTO \"values\" (name, parent_id, value_text, valid_from) \
VALUES('%s', %i, '%s', %i)" % (db_safe_str(name), parent_id, \
                               db_safe_str(value), valid_from)

    def add_default_value_int_param(self, name, parent_id, value,
                                    valid_from):
        return "\
INSERT INTO \"values\" (name, parent_id, value_int, valid_from) \
VALUES('%s', %i, %i, %i)" % (db_safe_str(name), parent_id, value,\
                             valid_from)

    def add_default_value_flt_param(self, name, parent_id, value,
                                    valid_from):
        return "\
INSERT INTO \"values\" (name, parent_id, value_real, valid_from) \
VALUES('%s', %i, %g, %i)" % (db_safe_str(name), parent_id, value,\
                             valid_from)

    def add_default_value_file_param(self, name, parent_id, value,
                                     valid_from):
        return "\
INSERT INTO \"values\" \
(name, parent_id, 'value_file_id', valid_from) \
VALUES('%s', %i, %g, %i)" % (db_safe_str(name), parent_id, value,\
                             valid_from)

    def get_value(self, parent_id, now):
        return "\
SELECT id, name, value_text, value_int, value_real, value_file_id \
FROM \"values\" \
WHERE parent_id=%i AND valid_from<=%i AND \
(valid_to IS NULL OR valid_to>%i)" % (parent_id, now, now)

    def get_value_by_name(self, parent_id, name, now):
        return "\
SELECT id, name, value_text, value_int, value_real, value_file_id \
FROM \"values\" \
WHERE parent_id=%i AND valid_from<=%i AND \
(valid_to IS NULL OR valid_to>%i) AND \
name='%s'" % (parent_id, now, now, db_safe_str(name))

    def add_null_value(self, name, valid_from, parent_id):
        return "\
INSERT INTO \"values\" (name, parent_id, valid_from) \
VALUES('%s', %i, %i)" % \
(db_safe_str(name), parent_id, valid_from)

    def add_value(self, name, value_column, value, valid_from, parent_id):
        return "\
INSERT INTO \"values\" (name, %s, parent_id, valid_from) \
VALUES('%s',%s, %i, %i)" % \
(db_safe_name(value_column), db_safe_str(name), value, parent_id, valid_from)

    def get_result_values_parent_id(self):
        return "SELECT id FROM \"values\" WHERE parent_id IS NULL AND \
name='results_values'"

    def disable_value_by_name(self, parent_id, name, now):
        return "\
UPDATE \"values\" SET valid_to=%i WHERE name='%s' AND parent_id=%i" % \
(now, name, parent_id)

    def disable_value(self, value_id, now):
        return "\
UPDATE \"values\" SET valid_to=%i WHERE id=%i" % (now, value_id)

    def get_test_properties(self, group_entry_id):
        return "\
SELECT name, Value_text, value_int, value_real, value_file_id FROM \
test_group_entry_properties JOIN \"values\" ON \"values\".id = Value_id \
WHERE test_group_entry_properties.group_entry_id=%i" % group_entry_id

    def get_dynamic_table_info(self):
        return '\
SELECT (SELECT value_text FROM "values" WHERE name=\'dev_table\' AND parent_id=2) as dev_table,\
(SELECT value_text FROM "values" WHERE name=\'dev_results_table\' AND parent_id=2) as dev_results_table,\
(SELECT value_text FROM "values" WHERE name=\'dev_results_table_key\' AND parent_id=2) as dev_results_table_key,\
(SELECT value_text FROM "values" WHERE name=\'dev_results_values_table\' AND parent_id=2) as dev_results_values_table,\
(SELECT value_int FROM \"values\" WHERE id=1) as db_version'

    def use_dynamic_table_info(self, row):
        self.devices_table_name           = row[0]
        self.dev_result_table_name        = row[1]
        self.device_key_name              = row[2]
        self.dev_result_values_table_name = row[3]
        self.db_version                   = row[4]
    """
    ====================================================================

     Tester Machine related SQL

    """
    _MACHINE_SQL="SELECT id, mac, hostname FROM tester_machines WHERE "

    def get_machine_by_id(self, machine_id):
        return self._MACHINE_SQL + "id=%u" % machine_id

    def get_machine(self, mac, hostname):
        return self._MACHINE_SQL + "mac='%s' AND lower(hostname)='%s'" % \
            (db_safe_str(mac).lower(), db_safe_str(hostname).lower())

    def add_machine(self, mac, hostname):
        return "INSERT INTO tester_machines (mac, hostname) \
        VALUES('%s','%s')" % (db_safe_str(mac).lower(),
            db_safe_str(hostname))
