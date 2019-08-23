
from dt_db_base import sql_common, db_safe_str

class example_sql_common(sql_common):
    """
    ====================================================================

    Overrides to example tables instead of dev

    """
    dev_result_table_name = "example_dev_test_results"
    dev_result_values_table_name = "example_dev_test_results_values"
    devices_table_name = "example_devs"
    device_key_name = "example_dev_id"

    def create_dev(self, serial_number, uuid):
        return "INSERT INTO example_devs (serial_number, uid) "\
               "VALUES('%s', '%s')" % (db_safe_str(serial_number),
                                       db_safe_str(uuid))
