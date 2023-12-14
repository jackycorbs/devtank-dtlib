import os
import sys

def _open_sqlite_db(db_def):
    from .database_sqlite import sqlite_db_backend
    return sqlite_db_backend(db_def)

def _open_mssql_db(db_def):
    from .database_mssql import mssql_db_backend
    return mssql_db_backend(db_def)

def _open_mysql_db(db_def):
    from .database_mysql import mysql_db_backend
    return mysql_db_backend(db_def)

def _open_pg_db(db_def):
    from .database_pg import pg_db_backend
    return pg_db_backend(db_def)


def get_default_schema(context):
    resource_dir = context.resource_dir
    schema_base_path = os.path.join(resource_dir,"db_base.sql")
    schema_path = os.path.join(resource_dir, "db.sql")

    r = ""
    with open(schema_base_path) as f:
        r += f.read()
    r += ";"
    with open(schema_path) as f:
        r += f.read()
    return r


def base_open_db_backend(context):

    db_def = context.db_def

    db_backends = {'sqlite' : _open_sqlite_db,
                   'mssql'  : _open_mssql_db,
                   'mysql'  : _open_mysql_db,
                   'pg'     : _open_pg_db}

    db_backend = db_backends[db_def['type']](db_def)
    work_folder = db_def['work_folder']
    get_schema = db_def.get('fn_get_schema', get_default_schema)
    extra_load = db_def.get('fn_extra_load', None)

    if not db_backend.is_empty():
        r = db_backend.open(work_folder)
    else:
        assert get_schema, "Empty database and no schema to fill it."
        schema = get_schema(context)
        if isinstance(schema, str):
            schema = schema.split(";")
            schema = [ line.strip() for line in schema ]
            schema = [ "" if line.lower() == "begin transaction" or \
                line.lower() == "commit" else line for line in schema ]
            schema = list(filter(lambda line: len(line), schema))
        db_backend.load(schema)
        r = db_backend.open(work_folder)
        if r:
            r.load_filestores(db_def)
    if extra_load and r:
        extra_load(r)
    return r
