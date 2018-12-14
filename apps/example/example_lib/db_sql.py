
from dt_db_base import sql_common, db_safe_str

class example_sql_common(sql_common):
    """
    ====================================================================

    Overrides to example tables instead of dev

    """
    dev_result_table_name = "example_dev_test_results"
    devices_table_name = "example_devs"
    device_key_name = "example_dev_id"

    _example_dev_SQL="\
    SELECT serial_number, id, uid FROM example_devs "

    def get_example_dev_by_serial(self, serial_number):
        return example_sql_common. _example_dev_SQL + "\
WHERE serial_number='%s'" % db_safe_str(serial_number)

    def get_example_dev_by_uid(self, uuid):
        return example_sql_common._example_dev_SQL + "\
WHERE uid='%s'" % db_safe_str(uuid)

    def get_example_dev_by_id(self, example_dev_id):
        return example_sql_common._example_dev_SQL + "\
WHERE id=%i" % example_dev_id

    def dev_latest_results(self, dev_id):
        return "\
SELECT example_dev_test_results.id, pass_fail, test_group_id, \
    test_groups.name, group_result_id \
FROM example_dev_test_results \
JOIN test_group_entries ON\
    example_dev_test_results.group_entry_id=test_group_entries.id \
JOIN test_groups ON test_group_id=test_groups.id \
WHERE example_dev_test_results.example_dev_id=%i" % dev_id

    def create_dev(self, serial_number, uuid):
        return "INSERT INTO example_devs (serial_number, uid) "\
               "VALUES('%s', '%s')" % (db_safe_str(serial_number),
                                       db_safe_str(uuid))
