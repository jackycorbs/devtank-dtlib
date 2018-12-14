import weakref


class null_safe_ref(object):
    def __init__(self, obj):
        self._obj = weakref.ref(obj) if obj else None

    def get(self):
        return self._obj() if self._obj else None


class db_child(object):
    def __init__(self, db, db_id=None, db_serial=None, db_extra=None):
        self._db = null_safe_ref(db)
        self.id = db_id
        self.serial_number = db_serial
        db_obj_type = type(self)
        db_obj_type_maps = db_child._get_db_obj_type_maps(db, db_obj_type)
        ref_link = weakref.ref(self)
        if db_id is not None:
            db_obj_type_maps['id'][db_id] = ref_link
        if db_serial is not None:
            db_obj_type_maps['serial'][db_serial] = ref_link
        if db_extra is not None:
            db_obj_type_maps['extra'][db_extra] = ref_link

        db._known_objs[db_obj_type] = db_obj_type_maps

    @property
    def db(self):
        return self._db.get()

    @staticmethod
    def _get_db_obj_type_maps(db, db_obj_type):
        return db._known_objs.get(db_obj_type, {'id': {},
                                                'serial':{},
                                                'extra':{}})

    @staticmethod
    def _set(db, key, cache_key, db_obj_type, instance):
        if key is None:
            return None
        db_obj_type_maps = db_child._get_db_obj_type_maps(db, db_obj_type)
        if instance:
            db_obj_type_maps[cache_key][key] = weakref.ref(instance)
        else:
            db_obj_type_maps[cache_key].pop(key, None)

    @staticmethod
    def _swap(db, old_key, new_key, cache_key, db_obj_type):
        db_obj_type_maps = db_child._get_db_obj_type_maps(db, db_obj_type)
        known_map = db_obj_type_maps[cache_key]
        r = known_map.pop(old_key, None)
        if r is not None and new_key is not None:
            known_map[new_key] = r

    @staticmethod
    def _get(db, key, cache_key, sql_cmd, db_obj_type):
        if key is None:
            return None
        db_obj_type_maps = db_child._get_db_obj_type_maps(db, db_obj_type)
        known_map = db_obj_type_maps[cache_key]
        r = known_map.get(key, None)
        if r:
            r = r()
            if r:
                return r
        cmd = sql_cmd(key)
        row = db.db.query_one(cmd)
        if row is None:
            return None
        return db_obj_type(db, *row)

    @staticmethod
    def _get_by_id(db, db_obj_type, sql_cmd, db_id):
        return db_child._get(db, db_id, 'id', sql_cmd, db_obj_type)

    @staticmethod
    def _get_by_serial(db, db_obj_type, sql_cmd, db_serial):
        return db_child._get(db, db_serial, 'serial', sql_cmd, db_obj_type)

    @staticmethod
    def _get_by_extra(db, db_obj_type, sql_cmd, db_extra):
        return db_child._get(db, db_extra, 'extra', sql_cmd, db_obj_type)


class lazy_id_to_db_child(object):
    def __init__(self, db, db_id, db_child_type):
        self._db = null_safe_ref(db)
        self._db_id = db_id
        self.db_child_type = db_child_type
        self._cache = null_safe_ref(None)

    @property
    def db(self):
        return self._db.get()

    def get(self):
        r = self._cache.get()
        if r:
            return r
        if not self._db_id:
            return None
        r = self.db_child_type.get_by_id(self.db, self._db_id)
        self._cache = null_safe_ref(r)
        return r
