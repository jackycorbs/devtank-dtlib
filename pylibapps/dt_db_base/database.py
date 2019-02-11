'''

TODO: Really this should always be called a different thread than the GUI thread while the GUI thread has a waiting indicator.

'''

import os
import copy
import yaml
import hashlib

from test_file_extract import get_args_in_src
from db_filestore_protocol import smb_transferer, sftp_transferer

from db_common import *
from db_tests import test_script_obj, test_group_obj, test_group_sessions

import db_values


def _get_defaults(local_folder):
    defaults_file = os.path.join(local_folder, "args.yaml")
    if os.path.exists(defaults_file):
        with open(defaults_file) as f:
            return yaml.load(f)
    return {}

def _extract_defaults(test_file, default_args):
    args = get_args_in_src(test_file)
    for key in args:
        args[key] = default_args[key]
    return args


def filename_sha256(filename):
    m = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            m.update(chunk)
    return str(m.hexdigest())


class tester_database(object):
    def __init__(self, db, sql, work_folder):
        self.db = db
        self.sql = sql
        self.version = db_values.get_db_version(db, sql)
        self.work_folder = work_folder
        self._known_objs = {}
        self.protocol_transferers = {sftp_transferer.protocol_id : sftp_transferer(),
                                     smb_transferer.protocol_id  : smb_transferer() }
        if not os.path.exists(work_folder):
            os.mkdir(work_folder)

    def clean(self):
        for protocol_transferer in self.protocol_transferers.values():
            protocol_transferer.clean()
        self.db.clean()

    def get_filestore_protocol_id(self, protocol_name):
        cmd = self.sql.get_file_store_protocol_id(protocol_name)
        row = self.db.query_one(cmd)
        if row is None:
            return None
        return row[0]

    def add_filestore(self, host, folder, writable, protocol_id):
        host = host.upper()
        db = self.db
        sql = self.sql

        c = db.cursor()
        found = False

        rows = c.query(sql.get_all_file_stores())
        for row in rows:
            if row[1].upper() == host:
                if row[2] == folder and row[3] == protocol_id:
                    rw = True if row[4] else False
                    writable = True if writable else False
                    if rw != writable:
                        c.update(sql.update_file_store_writable(row[0], 1 if writable else 0))
                    found = True
                    break

        if not found:
            c.insert(sql.add_file_store(host, folder, 1 if writable else 0, protocol_id ))
        db.commit()

    def _new_test_group(self, *args):
        return test_group_obj(self, *args)

    def _new_test_obj(self, *args):
        return test_script_obj(self, *args)

    def get_all_tests(self):
        now = db_ms_now()
        rows = self.db.query(self.sql.get_all_tests(now))
        return [ self._new_test_obj( row[0], row[1], row[2]) for row in rows ]

    def get_deleted_tests(self):
        now = db_ms_now()
        rows = self.db.query(self.sql.get_deleted_tests(now))
        return [ self._new_test_obj( row[0], row[1], row[2]) for row in rows ]

    def get_groups(self):
        now = db_ms_now()
        rows = self.db.query(self.sql.get_groups(now))
        return [self._new_test_group(*row) for row in rows ]

    def get_group_by_id(self, group_id):
        cmd = self.sql.get_group_by_id(group_id)
        rows = self.db.query(cmd)
        if not len(rows):
            return None
        row = rows[0]
        return self._new_test_group( *row)

    def get_group(self, group_name):
        now = db_ms_now()
        cmd = self.sql.get_group_by_name(group_name, now)
        rows = self.db.query(cmd)
        if not len(rows):
            return None
        row = rows[0]
        return self._new_test_group( *row)

    def _add_files(self, c, filepaths, now=None):
        file_store = c.query_one(self.sql.get_rw_file_store())
        file_store_id = file_store[0]
        file_store_host = file_store[1]
        file_store_folder = file_store[2]
        protocol_id = file_store[3]

        if now is None:
            now = db_ms_now()

        if protocol_id not in self.protocol_transferers:
            raise Exception("Unknown protocol for filestore.")

        protocol_transferer = self.protocol_transferers[protocol_id]

        protocol_transferer.open(file_store_host, file_store_folder)

        r = []

        for filepath in filepaths:
            filename = os.path.basename(filepath)
            stat = os.stat(filepath)
            mod_time = db_time(stat.st_mtime)
            file_size = stat.st_size
            file_id = c.insert(self.sql.add_file(filename,
                file_store_id, now, mod_time, file_size))
            if not file_id:
                raise Exception("Adding file \"%s\" failed" % filename)
            protocol_transferer.upload(filepath, file_id)
            r += [ file_id ]

        return r

    def add_files(self, filepaths):
        db = self.db
        r = self._add_files(db.cursor(), filepaths)
        db.commit()
        return r

    def get_file_to_local(self, file_id):
        row = self.db.query_one(self.sql.get_file_filestore(file_id))
        file_store_host = row[0]
        file_store_protocol_id = row[1]
        file_store_folder = row[2]
        name = row[3]
        mod_time = row[4]
        file_size = row[5]
        local_folder = os.path.join(self.work_folder, str(file_id))
        local_file = os.path.join(local_folder, name)
        if os.path.exists(local_file):
            stat = os.stat(local_file)
            local_mod_time = db_time(stat.st_mtime)
            local_file_size = stat.st_size
            time_delta = abs(local_mod_time - mod_time)
            # Allow 1 millisecond of difference due to float/int and filesystem storage.
            if time_delta < 2 and local_file_size == file_size:
                return local_file
        elif not os.path.exists(local_folder):
            os.mkdir(local_folder)

        if file_store_protocol_id not in self.protocol_transferers:
            raise Exception("Unknown protocol for filestore.")

        protocol_transferer = self.protocol_transferers[file_store_protocol_id]

        protocol_transferer.open(file_store_host, file_store_folder)

        mod_time = db2py_time(mod_time)

        protocol_transferer.download(local_file, file_id, mod_time)

        return local_file

    def get_settings(self):
        return db_values.get_settings_tree(self.db, self.sql, db_ms_now())

    def get_resource_files(self):
        rows = self.db.query(self.sql.get_resource_files())
        return dict([ row for row in rows ])

    def get_filename(self, file_id):
        row = self.db.query_one(self.sql.get_filename(file_id))
        if row is None:
            return None
        return row[0]

    def get_file_id_by_name(self, name, db_cursor=None):
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor
        row = c.query_one(self.sql.get_file_by_name(name))
        if row is None:
            return None
        return row[0]

    def set_defaults(self, args, db_cursor=None, now=None):
        db = self.db
        c = db_cursor
        if c is None:
            c = db.cursor()
        if now is None:
            now = db_ms_now()
        db_values.set_defaults(self.add_files, args, c, self.sql, now)
        db.commit()

    def get_test_by_name(self, test_name, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor
        cmd = self.sql.get_test_by_name(test_name, now)
        row = c.query_one(cmd)
        if row is None:
            return None
        return self._new_test_obj( row[0], row[1], row[2])

    def get_test_by_id(self, test_id, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor
        row = c.query_one(self.sql.get_test_by_id(test_id, now))
        if row is None:
            return None
        return self._new_test_obj( row[0], row[1], row[2])

    def add_test(self, local_file, args, db_cursor=None, now=None, test_name=None):
        if now is None:
            now = db_ms_now()
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor

        test_name = test_name if test_name else os.path.basename(local_file)

        existing = self.get_test_by_name(test_name, c, now)

        if existing:
            raise Exception("Test called \"%s\" already exists." % test_name)

        file_id = self._add_files(c, [local_file])[0]
        test_id = c.insert(self.sql.add_test(file_id, now))
        self.set_defaults(args, c, now)
        if db_cursor is None:
            db.commit()
        return self._new_test_obj( test_id, test_name, file_id)

    def _update_groups_with_new_test(self, groups, old_test, new_test):
        for group in groups:
            for n in range(0, len(group.tests)):
                test = group.tests[n]
                if test.id == old_test.id:
                    group.tests[n] = new_test
                    new_test.pending_properties = \
                        test.pending_properties
            group.updated_db()


    def update_tests_in_folder(self, local_folder, db_cursor=None, now=None):
        from tests_group import tests_group_creator

        if now is None:
            now = db_ms_now()
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor

        db_groups = self.get_groups()

        groups = [ tests_group_creator(self, db_group) \
                   for db_group in db_groups ]

        tests = self.get_all_tests()
        tests_map = dict([(test.filename, test) for test in tests])

        default_args = _get_defaults(local_folder)

        all_files = os.listdir(local_folder)
        for filename in all_files:
            if filename.endswith(".py"):
                new_test_file = os.path.join(local_folder, filename)
                if filename in tests_map:
                    test = tests_map[filename]
                    local_test_file = test.get_file_to_local()
                    test_filehash = filename_sha256(local_test_file)
                    new_file_hash = filename_sha256(new_test_file)
                    if test_filehash != new_file_hash:
                        print 'Updating test "%s"' % filename
                        test.remove(c, now)
                        args = _extract_defaults(new_test_file,
                                                 default_args)
                        new_test = self.add_test(new_test_file, args, c,
                                                 now)
                        self._update_groups_with_new_test(groups,
                                                          test,
                                                          new_test)
                else:
                    args = _extract_defaults(new_test_file,
                                             default_args)
                    new_test = self.add_test(new_test_file, args, c,
                                             now)
        if db_cursor is None:
            db.commit()


    def add_tests_folder(self, local_folder, db_cursor=None, now=None):
        r = []
        if now is None:
            now = db_ms_now()
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor

        default_args = _get_defaults(local_folder)
        all_files = os.listdir(local_folder)

        for test_filename in all_files:
            test_file = os.path.join(local_folder, test_filename)
            if test_file.endswith(".py"):
                args = _extract_defaults(test_file, default_args)
                test_obj = self.add_test(test_file, args, c, now)
                r += [test_obj]
        if db_cursor is None:
            db.commit()
        return r

    def group_from_dict(self, group_data, folder=None, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor

        default_args = _get_defaults(folder)
        tests = []
        for test_name, test_args in group_data["tests"]:
            if 'exit_on_fail' not in test_args:
                test_args['exit_on_fail'] = True
            test_obj = self.get_test_by_name(test_name, c, now)
            if not test_obj:
                assert folder
                test_filename = os.path.join(folder, test_name)
                if not os.path.exists(test_filename):
                    raise Exception("Test file '%s' not found" % test_filename)
                args = _extract_defaults(test_filename, default_args)
                test_obj = self.add_test(test_filename, args, c, now, test_name)
            for arg_key in test_args:
                arg_details = default_args[arg_key]
                if arg_details['type'] == 'file':
                    filename = test_args[arg_key]
                    if isinstance(filename, str):
                        file_id = self.get_file_id_by_name(filename, c)
                        if file_id is None:
                            filename = os.path.abspath(os.path.join(folder, filename))
                            file_id = self._add_files(c, [filename])[0]
                        test_args[arg_key] = (file, filename, file_id)
            test_obj.pending_properties = test_args
            tests += [test_obj]

        test_used = {}
        for test in tests:
            if test.filename in test_used:
                count = test_used[test.filename]
                test.name += "#%02i" % count
                test_used[test.filename] = count + 1
            else:
                test_used[test.filename] = 1

        r = self.add_group(group_data["name"],
                           group_data["desc"],
                           tests, c, now)

        if db_cursor is None:
            db.commit()

        return r

    def load_groups(self, filename):
        db = self.db
        c = db.cursor()
        now = db_ms_now()
        r = []
        folder = os.path.dirname(filename)
        with open(filename) as f:
            root_def = yaml.load(f)

            templates = root_def.get('templates', {})
            groups_list = root_def['groups']

            for group_data in groups_list:
                template_name = group_data.get('template', None)
                if template_name:
                    template_tests = templates.get(template_name, None)
                    if not template_tests:
                        raise Exception("Template '%s' used but not found." % template_name)

                    group_tests = group_data.get('tests', [])

                    for n in range(0, len(template_tests)):
                        template_test = template_tests[n]
                        if n == len(group_tests):
                            group_tests += [ copy.copy(template_test) ]
                        else:
                            group_test = group_tests[n]
                            if not len(group_test):
                                group_tests[n] = copy.copy(template_test)

                    group_data['tests'] = group_tests

                r += [self.group_from_dict(group_data, folder, c, now)]

            db.commit()
        return r

    def get_db_now():
        return None

    def add_group(self, name, desc, tests, db_cursor=None, now=None):
        if now is None:
            now = db_ms_now()
        db = self.db
        if db_cursor is None:
            c = db.cursor()
        else:
            c = db_cursor
        group_id = c.insert(self.sql.add_test_group(name, desc, now))

        group = self._new_test_group( group_id, name, desc)

        order_pos = 0
        for test in tests:
            group.add_test(test, c, order_pos, now)
            order_pos += 1

        if db_cursor is None:
            db.commit()

        return group

    def get_sessions(self, session_ids):
        assert len(session_ids)
        cmd = self.sql.get_sessions(session_ids)
        r = []
        for row in self.db.query(cmd):
            group = self._new_test_group( row[2], row[3], row[4])
            r += [ test_group_sessions(group, self, row[0], row[1]) ]
        return r

    def load_filestores(self, db_def):

        file_stores = db_def['file_stores']

        smbs = file_stores.get("smb", None)
        if smbs:
            for filestore in smbs:
                self.add_filestore(filestore[0], filestore[1], True,
                                   smb_transferer.protocol_id)

        sftps = file_stores.get("sftp", None)
        if sftps:
            for filestore in sftps:
                self.add_filestore(filestore[0], filestore[1], True,
                                   sftp_transferer.protocol_id)

    def get_dev(self, dev_uuid):
        raise Exception("Not implimented")
