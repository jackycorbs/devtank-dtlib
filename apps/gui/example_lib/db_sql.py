
from dt_db_base import sql_common, db_safe_str

class example_sql_common(sql_common):
    """
    ====================================================================

    Overrides to example tables instead of dev

    """
    def __init__(self):
        sql_common.__init__(self)
        self.dev_result_table_name = "example_dev_test_results"
        self.dev_result_values_table_name = "example_dev_test_results_values"
        self.devices_table_name = "example_devs"
        self.device_key_name = "example_dev_id"

    def create_dev(self, serial_number, uuid):
        return "INSERT INTO example_devs (serial_number, uid) "\
               "VALUES('%s', '%s')" % (db_safe_str(serial_number),
                                       db_safe_str(uuid))
