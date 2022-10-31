
from dt_db_base import sql_common, db_safe_str

class example_sql_common(sql_common):

    def create_dev(self, serial_number, uuid):
        return "INSERT INTO example_devs (serial_number, uid) "\
               "VALUES('%s', '%s')" % (db_safe_str(serial_number),
                                       db_safe_str(uuid))
