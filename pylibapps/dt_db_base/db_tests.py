from db_common import *
import db_values


class test_script_obj(object):
    def __init__(self, db, id, filename, file_id, name=None, group_entry_id=None, duration=None):
        self.db = db
        self.id = id
        self.name = name if name else filename
        self.filename = filename
        self.file_id = file_id
        self.group_entry_id = group_entry_id
        self._duration = duration
        self.pending_properties = {}

    def get_file_to_local(self):
        return self.db.get_file_to_local(self.file_id)

    def __str__(self):
        return "%s : %i : %s" % (self.name, self.id, str(self.pending_properties))

    @property
    def duration(self):
        if self._duration is None:
            return self._duration
        return db2py_time(self._duration)

    @duration.setter
    def duration(self, duration):
        self._duration = db_time(duration)

    @property
    def run_arguments(self):
        return dict([
            (key, value[1] \
                if (isinstance(value, tuple) and value[0] is file) \
                else value)
            for key, value in self.pending_properties.items()])

    def load_properties(self):
        if self.group_entry_id is None:
            return {}

        r = db_values.get_test_properties( self.group_entry_id,
                                           self.db.db,
                                           self.db.sql,
                                           self.db.get_file_to_local)
        self.pending_properties = r
        return r

    def remove(self, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        db = self.db.db
        sql = self.db.sql
        c = db_cursor
        if c is None:
            c = db.cursor()
        cmd = sql.remove_test(self.id, now)
        c.update(cmd)
        if db_cursor is None:
            db.commit()

    def restore(self, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        db = self.db.db
        c = db_cursor
        if c is None:
            c = db.cursor()
        self.id = c.insert(self.db.sql.add_test(self.file_id, now))
        if db_cursor is None:
            db.commit()


class test_group_obj:
    def __init__(self, db, id, name, desc):
        self.db = db
        self.id = id
        self.name = name
        self.desc = desc

    def __eq__(self, other):
        return self.id == other.id

    def get_tests(self):
        now = db_ms_now()
        rows = self.db.db.query(self.db.sql.get_tests(self.id, now))
        return [ test_script_obj(self.db, row[0], row[1], row[2], row[3], row[4], row[6]) for row in rows ]

    def get_duration(self):
        db = self.db.db
        now = db_ms_now()
        r = 0
        rows = db.query(self.db.sql.get_test_group_durations(self.id, now))
        for row in rows:
            if row[1] is None:
                return None
            r += row[1]
        return db2py_time(r)

    def add_test(self, test, db_cursor=None, order_pos=None, now=None):
        db = self.db.db
        sql = self.db.sql
        c = db_cursor
        if c is None:
            c = db.cursor()
        if order_pos is None:
            order_pos = 0
        if now is None:
            now = _ms_now()
        cmd=sql.add_test_group_test(self.id, test.id, test.name, order_pos, now)
        test.group_entry_id = c.insert(cmd)
        if "exit_on_fail" not in test.pending_properties:
            test.pending_properties["exit_on_fail"] = True
        for prop in test.pending_properties:
            prop_value = test.pending_properties[prop]
            value_id = db_values.add_value(self.db._add_files, c, sql,
                                           prop, prop_value, now)
            c.insert(sql.add_test_group_value(test.group_entry_id,
                                              value_id))
        if db_cursor is None:
            db.commit()

    def remove_test(self, test, db_cursor=None, now=None):
        if now is None:
            now = _ms_now()
        c = db_cursor
        if c is None:
            c = db.cursor()
        cmd = self.db.sql.remove_test_group_tests(test.group_entry_id, now)
        c.update(cmd)
        if db_cursor is None:
            db.commit()

    def update(self, name, desc, tests, db_cursor=None, now=None):
        db = self.db.db
        if db_cursor:
            c = db_cursor
        else:
            c = db.cursor()
        group_id = self.id

        sql = self.db.sql

        if (name != self.name):
            c.update(sql.set_test_group_name(group_id, name))

        if (desc != self.desc):
            c.update(sql.set_test_group_desc(group_id, desc))

        if not now:
            now = db_ms_now()

        old_tests = self.get_tests()

        if len(old_tests) > len(tests):
            for dead_test in old_tests[len(tests):]:
                self.remove_test(dead_test, c, now)
            old_tests = old_tests[:len(tests)]

        for old_test in old_tests:
            old_test.load_properties()

        for n in range(0, len(tests)):
            new_test = tests[n]
            old_test = old_tests[n] if n < len(old_tests) else None
            if str(old_test) != str(new_test):
                if old_test:
                    self.remove_test(old_test, c, now)
                self.add_test(new_test, c, n, now)

        if not db_cursor:
            db.commit()

    def delete(self, db_cursor=None, now=None):
        db = self.db.db
        if db_cursor:
            c = db_cursor
        else:
            c = db.cursor()
        if not now:
            now = db_ms_now()
        c.update(self.db.sql.remove_test_group(self.id, now))
        if not db_cursor:
            db.commit()

    def add_tests_results(self, results, tests, db_cursor=None, now=None):
        db = self.db.db
        if db_cursor:
            c = db_cursor
        else:
            c = db.cursor()
        if not now:
            now = db_ms_now()

        sql = self.db.sql

        cmd = sql.add_test_group_results(self.id, now)
        results_id = c.insert(cmd)

        for dev_uuid, uuid_results in results.items():
            uuid_test_results = uuid_results['tests']
            old_uuid = uuid_results.get('old_uuid', None)

            for test in tests:
                test_data = uuid_test_results.get(test.name, None)
                if test_data:
                    pass_fail = test_data.get('passfail', None)
                    output = test_data.get('outfile', None)
                    log = test_data.get('logfile', None)
                    duration = test_data.get('duration', None)
                    values = test_data.get('stored_values', None)
                else:
                    pass_fail = False
                    output = None
                    log = None
                    duration = None
                    values = None

                if test.duration is None and duration is not None:
                    test.duration = duration

                group_entry_id = test.group_entry_id

                files = []
                if output:
                    files += [output]
                if log:
                    files += [log]
                file_ids = self.db._add_files(c, files)
                if log:
                    log = file_ids.pop()
                if output:
                    output = file_ids.pop()

                dev = self.db.get_dev(dev_uuid)
                if not dev and old_uuid:
                    dev = self.db.get_dev(old_uuid)
                    if dev:
                        dev.update_uuid(dev_uuid)
                if dev:
                    result_id = c.insert(sql.add_dev_result(results_id,
                                                  dev.id,
                                                  group_entry_id,
                                                  pass_fail,
                                                  output, log,
                                                  db_time(duration)))
                    if values:
                        if sql.dev_result_values_table_name:
                            for test_value_name, test_value_data in values.items():
                                value_id = db_values.add_value(self.db._add_files, c, sql,
                                                               test_value_name, test_value_data, now)
                                c.insert(sql.add_test_value(result_id, value_id))
                        else:
                            print "Stored value but no table to put it."
                else:
                    print "Unknown UUID %s, can't store results." % dev_uuid
        if not db_cursor:
            db.commit()

    def get_sessions_count(self):
        cmd = self.db.sql.get_test_group_results_count(self.id)
        rows = self.db.db.query(cmd)
        return rows[0][0]

    def get_sessions(self, offset, count):
        cmd = self.db.sql.get_test_group_results(self.id, offset, count)
        rows = self.db.db.query(cmd)
        return [ test_group_sessions(self, self.db, *row) \
                 for row in rows ]

    def get_dev_last_pass_fail(self, dev_id):
        cmd = self.db.sql.dev_last_group_pass_fail(dev_id, self.id)
        r = self.db.db.query_one(cmd)
        if r is None:
            return None
        return bool(r[0])


class dev_results_builder(object):
    def __init__(self):
        self.pass_fail = False
        self.results = []

    def set_result(self, index, name, pass_fail, out_file_id, log_file_id):
        self.results += [(False,)] * (index - len(self.results) + 1)
        self.results[index] = (pass_fail, name, out_file_id, log_file_id)


class test_group_sessions(object):
    def __init__(self, group, db, id, db_time_of_tests):
        self.group = group
        self.db = db
        self.id = id
        self.time_of_tests = db2py_time(db_time_of_tests)
        self.pass_fail = True

        cmd = self.db.sql.get_dev_results(self.id)
        rows = self.db.db.query(cmd)

        devs = {}
        for row in rows:
            result_id   = row[0]
            dev_uuid    = row[1]
            pass_fail   = row[2]
            out_file_id = row[3]
            log_file_id = row[4]
            test_id     = row[5]
            test_name   = row[6]
            test_file   = row[7]
            order_pos   = row[8]
            if not test_name:
                test_name = test_file
            if not pass_fail:
                self.pass_fail = False
            if dev_uuid in devs:
                dev_results = devs[dev_uuid]
            else:
                dev_results = dev_results_builder()
                devs[dev_uuid] = dev_results

            dev_results.set_result(order_pos, test_name, pass_fail, out_file_id, log_file_id)

        for dev in devs:
            dev_results = devs[dev]
            if len(dev_results.results):
                dev_results.pass_fail = min([result[0] for result in dev_results.results])

        self.devices = devs

        all_tests = []
        cmd = self.db.sql.get_test_group_results_tests(self.id, db_time_of_tests)
        rows =  self.db.db.query(cmd)
        for row in rows:
            order_pos   = row[0]
            test_name   = row[1]
            test_file   = row[2]
            if not test_name:
                test_name = test_file
            all_tests += [None] * (order_pos - len(all_tests) + 1)
            all_tests[order_pos] = test_name
        self.tests = all_tests
