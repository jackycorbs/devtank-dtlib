
from db_common import *

_id_null = lambda x: ("%i" % x) if x else "NULL"
_int_null = lambda x: ("%i" % x) if x is not None else "NULL"


class sql_common(object):

    dev_result_table_name = "dev_result_table"
    devices_table_name = "devs"
    device_key_name = "dev_id"

    """
    ====================================================================

     Device related SQL

    """
    def get_update_dev_uid(self, dev_id, new_uuid):
        return "\
UPDATE %s SET uid='%s' WHERE id=%i" % \
(self.devices_table_name, db_safe_str(new_uuid), dev_id)

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
        dev_result_table_name = self.__class__.dev_result_table_name
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
        return "\
SELECT tests.id, filename, file_id, test_group_entries.name, \
       test_group_entries.id AS entry_id, order_position \
FROM tests \
JOIN files ON tests.file_id=files.id \
JOIN test_group_entries ON test_group_entries.Test_id=tests.id \
WHERE (test_group_entries.valid_to IS NULL OR \
test_group_entries.valid_to>%i) AND \
test_group_entries.valid_from<=%i AND \
test_group_entries.test_group_id=%i \
ORDER BY order_position " % (now, now, group_id)

    def set_test_duration(self, group_entry_id, duration):
        return "\
UPDATE test_group_entries SET duration=%i WHERE id=%i AND \
    (duration IS NULL OR duration < %i)" % (
    duration, group_entry_id, duration)

    """
    ====================================================================

     tests group related SQL

    """
    def add_test_group(self, name, desc, valid_from):
        return "\
INSERT INTO test_groups (name, description, valid_from) \
VALUES('%s', '%s', %i)" % (db_safe_str(name), db_safe_str(desc), valid_from)

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
        return sql_common._GROUP_SQL + "\
WHERE valid_from<=%i AND (valid_to IS NULL OR valid_to>%i)" % \
(now, now)

    def get_group_by_name(self, name, now):
        return sql_common._GROUP_SQL + "\
WHERE valid_from<=%i AND (valid_to IS NULL OR valid_to>%i) \
AND name='%s'" % (now, now, db_safe_str(name))

    def get_group_by_id(self, group_id):
        return sql_common._GROUP_SQL + " WHERE id=%i" % group_id

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
        return "\
SELECT duration FROM test_group_entries WHERE \
test_group_id=%i AND \
valid_from<=%i AND \
(valid_to IS NULL OR valid_to>%i)" % (group_id, now, now)

    """
    ====================================================================

     results related SQL

    """
    def add_test_group_results(self, group_id, now):
        return "\
INSERT INTO test_group_results (group_id, Time_Of_tests) \
VALUES (%i, %i)" % (group_id, now)

    def get_test_group_results_count(self, group_id):
        return "\
SELECT COUNT(id) FROM test_group_results WHERE group_id=%i" % \
group_id

    def get_test_group_results(self, group_id, offset, count):
        return "\
SELECT id, Time_Of_tests FROM test_group_results WHERE group_id=%i \
ORDER BY Time_Of_tests DESC LIMIT %u OFFSET %u" % (group_id, count, offset)

    def get_sessions(self, session_ids):
        return "\
SELECT test_group_results.id, Time_Of_tests, \
    group_id, name, description \
FROM test_group_results JOIN test_groups ON test_groups.id = group_id \
WHERE test_group_results.id IN (%s) ORDER BY Time_Of_tests DESC" % \
",".join([str(session_id) for session_id in session_ids])

    def get_dev_results(self, session_id):
        dev_result_table_name = self.__class__.dev_result_table_name
        devices_table_name = self.__class__.devices_table_name
        device_key_name = self.__class__.device_key_name
        return "\
SELECT %s.id, %s.uid, pass_fail, output_file_id,\
      log_file_id, Test_id, name, filename, order_position \
FROM %s \
JOIN test_group_entries ON \
    test_group_entries.id = %s.group_entry_id \
JOIN tests ON tests.id = test_group_entries.Test_id \
JOIN files ON files.id = tests.file_id \
JOIN %s ON %s.id = %s.%s \
WHERE %s.group_result_id=%i" % \
 (dev_result_table_name, devices_table_name, dev_result_table_name, \
  dev_result_table_name, devices_table_name, devices_table_name, \
  dev_result_table_name, device_key_name, dev_result_table_name, \
  session_id)


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
        dev_result_table_name = self.__class__.dev_result_table_name
        device_key_name = self.__class__.device_key_name
        return "\
INSERT INTO %s \
(group_result_id, %s, group_entry_id, pass_fail, output_file_id,\
log_file_id, duration) \
VALUES (%i, %i, %i, %i, %s, %s, %s)" % \
 (dev_result_table_name, device_key_name, session_id, dev_id,
  group_entry_id, int(pass_fail), _id_null(output_file_id),\
  _id_null(log_file_id), _int_null(duration))
    """
    ====================================================================

     Values related SQL

    """
    defaults_id = 3
    settings_id = 2
    test_props_id = 4

    def get_version(self):
        return "SELECT name, value_int FROM \"values\" WHERE id=1"

    def add_default_value(self, name, valid_from):
        return "\
INSERT INTO \"values\" (name, parent_id, valid_from) \
VALUES('%s', %i, %i)" % \
(db_safe_str(name), sql_common.defaults_id, valid_from)

    def add_default_value_str_param(self, name, parent_id, value,
                                    valid_from):
        return "\
INSERT INTO \"values\" (name, parent_id, value_text, valid_from) \
VALUES('%s', %i, '%s', %i)" % (db_safe_str(name), parent_id, value,\
                               valid_from)

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
SELECT id FROM \"values\" \
WHERE parent_id=%i AND valid_from<=%i AND \
(valid_to IS NULL OR valid_to>%i) AND \
name='%s'" % (parent_id, now, now, db_safe_str(name))

    def add_null_value(self, name, valid_from):
        return "\
INSERT INTO \"values\" (name, parent_id, valid_from) \
VALUES('%s', %i, %i)" % \
(db_safe_str(name), sql_common.test_props_id, valid_from)

    def add_value(self, name, value_column, value, valid_from):
        return "\
INSERT INTO \"values\" (name, %s, parent_id, valid_from) \
VALUES('%s',%s, %i, %i)" % \
(db_safe_name(value_column), db_safe_str(name), value,
sql_common.test_props_id, valid_from)

    def disable_value_by_name(self, parent_id, name, now):
        return "\
UPDATE \"values\" SET valid_to=%i WHERE name='%s' AND parent_id=%i" % \
(now, name, parent_id)

    def get_test_properties(self, group_entry_id):
        return "\
SELECT name, Value_text, value_int, value_real, value_file_id FROM \
test_group_entry_properties JOIN \"values\" ON \"values\".id = Value_id \
WHERE test_group_entry_properties.group_entry_id=%i" % group_entry_id
