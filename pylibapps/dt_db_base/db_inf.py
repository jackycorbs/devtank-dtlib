import time

_db_debug_print = lambda msg : None


def set_debug_print(cb):
    global _db_debug_print
    _db_debug_print = cb


class db_cursor(object):
    def __init__(self, parent):
        self._parent = parent
        self._c      = parent._get_db().cursor()

    def _execute(self, cmd):
        self._parent._last_used = time.time()
        try:
            self._c.execute(cmd)
            _db_debug_print("SQL : '%s'" % cmd)
        except Exception as e:
            print 'SQL "%s" failed' % cmd
            raise e

    def query(self, cmd):
        self._execute(cmd)
        return self._c.fetchall()

    def query_one(self, cmd):
        self._execute(cmd)
        return self._c.fetchone()

    def update(self, cmd):
        self._execute(cmd)

    def insert(self, cmd):
        self._execute(cmd)
        return self._c.lastrowid


class db_inf(object):
    def __init__(self, db):
        self._db = db
        self._current = None
        self._cur_count = 0
        self._last_used = time.time()

    def _get_db(self):
        if not self._db:
            self.wake()
        return self._db

    def cursor(self):
        if self._current:
            return self._current
        return db_cursor(self)

    def commit(self):
        if not self._current:
            self._get_db().commit()

    def rollback(self):
        self._get_db().rollback()

    def query(self, cmd):
        return self.cursor().query(cmd)

    def query_one(self, cmd):
        return self.cursor().query_one(cmd)

    def update(self, cmd):
        c = self.cursor()
        c.update(cmd)
        if self._current is None:
            self.commit()

    def insert(self, cmd):
        c = self.cursor()
        r = c.insert(cmd)
        if self._current is None:
            self.commit()
        return r

    def __enter__(self):
        if not self._current:
            self._current = self.cursor()
        self._cur_count += 1
        self._last_used = time.time()
        return self._current

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cur_count -= 1
        if not self._cur_count:
            self._current = None
            self._last_used = time.time()

    def wake_fail_catch(self, e):
        pass

    def wake(self):
        pass

    @property
    def last_used(self):
        return self._last_used

    def clean(self):
        return not bool(self._current)
