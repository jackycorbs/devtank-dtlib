from __future__ import print_function, absolute_import

import os
import sys
import weakref

from .db_common import *



class value_obj_t(object):
    def __init__(self, parent_obj, db, value_id, value_name, value_text=None, value_int=None, value_real=None, value_file_id=None):
        self._parent = weakref.ref(parent_obj) if parent_obj else None
        self.id = value_id
        self.name = db_std_str(value_name)
        self._db =  weakref.ref(db)
        self.value = None

        if not value_text is None:
            self.value = value_text
        elif not value_int is None:
            self.value = value_int
        elif not value_real is None:
            self.value = value_real
        elif not value_file_id is None:
            filename = db.get_file_to_local(value_file_id)
            self.value = (dbfile, filename, value_file_id)

    @staticmethod
    def get_settings_root(db):
        return value_obj_t(None, db, db.sql.settings_id, "settings")

    @staticmethod
    def get_test_props_root(db):
        return value_obj_t(None, db, db.sql.test_props_id, "results_values")

    @staticmethod
    def get_result_props_root(db):
        rows = db.db.query(db.sql.get_result_values_parent_id())
        if not len(rows):
            return None
        assert len(rows) == 1, "Should be one entry for results values parent."
        return value_obj_t(None, db, rows[0][0], "results_values")

    @property
    def db(self):
        return self._db()

    @property
    def parent(self):
        return self._parent() if self._parent else None

    def get_children(self, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        c = db_cursor
        if c is None:
            c = self.db.db.cursor()
        value_entries = c.query(self.db.sql.get_value(self.id, now))
        return dict([(value_entry[1], value_obj_t(self, self.db, *value_entry)) for value_entry in value_entries])

    def get_child(self, name, now=None):
        if now is None:
            now = db_ms_now()
        cmd = self.db.sql.get_value_by_name(self.id, name, now)
        row = self.db.db.query_one(cmd)
        return value_obj_t(self, self.db, *row)

    @staticmethod
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
                r[name] = value_obj_t._get_value_tree(c, sql, value_entry[0], now)
        return r

    def get_as_dict_tree(self, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        c = db_cursor
        if c is None:
            c = self.db.db.cursor()
        return self._get_value_tree(c, self.db.sql, self.id, now)


    def add_dict_tree(self, d, db_cursor=None, now=None):
        self._set_dict_tree(d, True, db_cursor, now)

    def set_dict_tree(self, d, db_cursor=None, now=None):
        self._set_dict_tree(d, False, db_cursor, now)

    def _set_dict_tree(self, d, append, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        c = db_cursor
        if c is None:
            c = self.db.db.cursor()

        old_children = self.get_children()

        for name, value in d.items():
            child = old_children.pop(name, None)
            if not child:
                self.add_child(name, value, c, now)
            else:
                if isinstance(value, dict):
                    if child.value is None:
                        child._set_dict_tree(value, append, c, now)
                    else:
                        child.remove()
                        self.add_child(name, value, c, now)
                elif type(child.value) != type(value) or \
                  child.value != value:
                    child.remove()
                    self.add_child(name, value, c, now)

        if not append:
            # Remove anything left in old children array
            for old_child in old_children.values():
                old_child.remove(c, now)

        if db_cursor is None:
            self.db.db.commit()


    def remove(self, db_cursor=None, now=None):
        assert self.parent, "Can't remove a root value"
        if now is None:
            now = db_ms_now()
        c = db_cursor
        if c is None:
            c = self.db.db.cursor()

        c.update(self.db.sql.disable_value(self.id, now))

        if db_cursor is None:
            self.db.db.commit()


    def add_child(self, name, value, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        c = db_cursor
        if c is None:
            c = self.db.db.cursor()
        value_field = None
        if db_is_string(value):
            row = [value, None, None, None]
            value_field="Value_Text"
            value="'%s'" % value
        elif isinstance(value, int):
            row = [None, value, None, None]
            value_field="Value_Int"
            if isinstance(value, bool):
                value = int(value)
        elif isinstance(value, float):
            row = [None, None, value, None]
            value_field="Value_Real"
        elif isinstance(value, tuple):
            assert value[0] is dbfile
            value_field="Value_File_ID"
            if value[2] is None:
                r = self.db.add_files(c, [value[1]], now)
                value = list(value)
                value[2] = r[0]
            value = value[2]
            row = [None, None, None, value]

        if value_field:
            value_id = c.insert(self.db.sql.add_value(name, value_field, value, now, self.id))
            r = value_obj_t(self, self.db, value_id, name, *row)
        else:
            value_id = c.insert(self.db.sql.add_null_value(name, now, self.id))
            r = value_obj_t(self, self.db, value_id, name)
            if isinstance(value, dict):
                for child_name, child_value in value.items():
                    r.add_child(child_name, child_value, c, now)
            else:
                assert value is None, "Unknown value type"

        if db_cursor is None:
            self.db.db.commit()

        return r
