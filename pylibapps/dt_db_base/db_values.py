from __future__ import print_function, absolute_import

import os
import sys

from .db_common import *


def _get_value_tree(c, sql, parent_id, now):
    r = {}
    value_entries = c.query(sql.get_value(parent_id, now))
    for value_entry in value_entries:
        found=False
        name=db_std_str(value_entry[1])
        for value in value_entry[2:-1]:
            if value is not None:
                r[name] = db_std_str(value)
                found=True
                break
        if not found and not value_entry[-1] is None:
            row = c.query_one(sql.get_filename(value_entry[-1]))
            r[name] = (dbfile, db_std_str(row[0]), value_entry[-1])
        elif not found:
            r[name] = _get_value_tree(c, sql, value_entry[0], now)
    return r


def get_settings_tree(db, sql, now):
    return _get_value_tree(db.cursor(), sql, sql.settings_id, db_ms_now())


def _get_default_by_name(c, sql, prop_name, now):
    cmd = sql.get_value_by_name(sql.defaults_id, prop_name, now)
    return c.query(cmd)


def add_value(add_files, c, sql, prop_name, prop_value, valid_from, is_result=False):
    prop_type = ""
    if db_is_string(prop_value):
        prop_type="Value_Text"
        prop_value="'%s'" % prop_value
    elif isinstance(prop_value, int):
        prop_type="Value_Int"
        if isinstance(prop_value, bool):
            prop_value = int(prop_value)
    elif isinstance(prop_value, float):
        prop_type="Value_Real"
    elif isinstance(prop_value, tuple):
        assert prop_value[0] is dbfile
        prop_type="Value_File_ID"
        if prop_value[2] is None:
            r = add_files(c, [prop_value[1]])
            prop_value = list(prop_value)
            prop_value[2] = r[0]
        prop_value = prop_value[2]
    elif prop_value is None:
        return c.insert(sql.add_null_value(prop_name, valid_from, is_result))
    else:
        raise Exception("Unknown property type %s" % str(type(prop_value)))
    return c.insert(sql.add_value(prop_name, prop_type, prop_value, valid_from, is_result))




def set_defaults(add_files, args, c, sql, now):
    sql_cmds = {"int"  : sql.add_default_value_int_param,
                "bool" : sql.add_default_value_int_param,
                "float": sql.add_default_value_flt_param,
                "text" : sql.add_default_value_str_param,
                "file" : sql.add_default_value_file_param}
    for prop in args:
        prop_values = args[prop]

        prop_type = prop_values['type']
        if isinstance(prop_type, type):
            prop_pytype = prop_type
            prop_type = db_type_from_py_type(prop_type)
        else:
            prop_pytype = py_type_from_db_type(prop_type)

        existing = _get_default_by_name(c, sql, prop, now)
        if len(existing):
            default_value_id = existing[0][0]
            existing = _get_value_tree(c, sql, default_value_id, now)
            new_props = set()
            old_props = set()
            if existing["type"] == prop_type:
                new_props = set(prop_values.keys()) - set(existing.keys())
                old_props = set(existing.keys()) - set(prop_values.keys())
                for key in prop_values:
                    if key in existing:
                        new_value = prop_values[key]
                        old_value = existing[key]
                        if not key in ["desc", "type"]:
                            if prop_pytype is not dbfile:
                                new_value = prop_pytype(new_value)
                                old_value = prop_pytype(old_value)
                            else:
                                new_value = new_value[2]
                                old_value = old_value[2]

                        if str(new_value) != str(old_value):
                            entry = set({key:True})
                            old_props = old_props.union(entry)
                            new_props = new_props.union(entry)
            else:
                old_props = existing.keys()
                new_props = prop_values.keys()

            for old_prop in old_props:
                c.update(
                    sql.disable_value_by_name(default_value_id,
                                               old_prop, now))
            for new_prop in new_props:
                sql_cmd = sql_cmds[prop_type]
                new_value = prop_values[new_prop]
                if not new_prop in ["desc", "type"]:
                    if prop_pytype is not dbfile:
                        new_value = prop_pytype(new_value)
                    else:
                        if new_value[2] is None:
                            new_value = new_value[1]
                            assert os.path.exists(new_value)
                            file_ids = add_files([new_value])
                            new_value = file_ids[0]
                        else:
                            new_value = new_value[2]
                else:
                    sql_cmd = sql.add_default_value_str_param
                cmd = sql_cmd(new_prop,
                              default_value_id,
                              new_value,
                              now)
                c.insert(cmd)
            continue

        cmd = sql.add_default_value(prop, now)
        prop_id = c.insert(cmd)
        cmd = sql.add_default_value_str_param('desc', prop_id, prop_values['desc'], now)
        c.insert(cmd)
        cmd = sql.add_default_value_str_param('type', prop_id, prop_type, now)
        c.insert(cmd)
        sql_cmd = sql_cmds[prop_type]
        if prop_type == "int" or prop_type == "float":
            for param in ["min", "max", "step"]:
                cmd = sql_cmd(param, prop_id, prop_pytype(prop_values[param]), now)
                c.insert(cmd)
        if prop_type == "file":
            if 'default' in prop_values:
                file_value = prop_values['default']
                if not isinstance(file_value, int):
                    assert os.path.exists(file_value)
                    file_ids = add_files([file_value])
                    file_value = file_ids[0]
                cmd = sql_cmd('default', prop_id, file_value, now)
                c.insert(cmd)
        else:
            if 'default' in prop_values:
                cmd = sql_cmd('default', prop_id, prop_pytype(prop_values['default']), now)
                c.insert(cmd)
