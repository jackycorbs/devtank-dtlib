
def _open_sqlite_db(db_def):
    from database_sqlite import sqlite_db_backend
    return sqlite_db_backend(db_def)

def _open_mssql_db(db_def):
    from database_mssql import mssql_db_backend
    return mssql_db_backend(db_def)

def _open_mysql_db(db_def):
    from database_mysql import mysql_db_backend
    return mysql_db_backend(db_def)

def _open_pg_db(db_def):
    from database_pg import pg_db_backend
    return pg_db_backend(db_def)

def base_open_db_backend(db_def, get_schema, work_folder, extra_load=None):

    db_backends = {'sqlite' : _open_sqlite_db,
                   'mssql'  : _open_mssql_db,
                   'mysql'  : _open_mysql_db,
                   'pg'     : _open_pg_db}

    db_backend = db_backends[db_def['type']](db_def)

    if not db_backend.is_empty():
        return db_backend.open(work_folder)

    db_backend.load(get_schema())
    r = db_backend.open(work_folder)
    r.load_filestores(db_def)
    if extra_load:
        extra_load(r)
    return r
