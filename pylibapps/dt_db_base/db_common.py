import sys
import time

def db_time(py_time):
    if py_time is None:
        return None
    return int(1000000 * py_time)

def db2py_time(db_time):
    return db_time / 1000000.0

def db_ms_now():
    return db_time(time.time())

def db_safe_str(s):
    s = s.replace("'", '')
    s = s.replace('"', '')
    return s.rstrip('\0')

def db_safe_name(s):
    r = s.replace("'", '"')
    r.replace(" ","_")
    r.replace(";","_")
    return r.rstrip('\0')


if sys.version_info[0] < 3:
    dbfile = file
    db_is_string = lambda s : isinstance(s, str) or isinstance(s, unicode)
    db_std_str = lambda s : str(s) if isinstance(s, unicode) else s
else:
    from collections import namedtuple
    dbfile = namedtuple("dbfile", [])
    db_std_str = lambda s : s.decode() if isinstance(s, bytes) else s
    db_is_string = lambda s : isinstance(s, str) or isinstance(s, bytes)


def py_type_from_db_type(db_type):
    py_types = {"file": dbfile,
                "int": int,
                "float": float,
                "text": str,
                "bool": bool}
    return py_types[db_type]


def db_type_from_py_type(py_type):
    db_types = {bool : "bool",
                int : "int",
                float : "float:",
                dbfile : "file",
                str : "text"}
    return db_types[py_type]
