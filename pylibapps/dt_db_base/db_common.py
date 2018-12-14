import time

def db_time(py_time):
    return int(1000000 * py_time)

def db2py_time(db_time):
    return db_time / 1000000.0

def db_ms_now():
    return db_time(time.time())

def db_safe_str(s):
    r = s.replace("'", '"')
    return r.rstrip('\0')

def db_safe_name(s):
    r = s.replace("'", '"')
    r.replace(" ","_")
    r.replace(";","_")
    return r.rstrip('\0')


def db_de_unicode_str(s):
    return str(s) if isinstance(s, unicode) else s

def py_type_from_db_type(db_type):
    py_types = {"file": file,
                "int": int,
                "float": float,
                "text": str,
                "bool": bool}
    return py_types[db_type]


def db_type_from_py_type(py_type):
    db_types = {bool : "bool",
                int : "int",
                float : "float:",
                file : "file",
                str : "text"}
    return db_types[py_type]
