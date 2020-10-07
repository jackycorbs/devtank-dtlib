import sys


if sys.version_info[0] < 3:
    from db_sql import sql_common
else:
    from .db_sql import sql_common


class mssql_sql_overload(sql_common):
    def get_rw_file_store(self):
        return "SELECT TOP(1) ID, Server_Name, Base_Folder, Protocol_ID FROM \
File_Stores WHERE Is_Writable=1"
