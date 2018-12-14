import os

from db_common import py_type_from_db_type

class tests_group_creator:
    def __init__(self, db, db_group=None):
        self.db = db
        self.tests = []
        self.props_defaults = {}
        self.name = ""
        self.description = ""
        self.db_group = None
        self.duration = None
        self.passed = False
        if db:
            self.update_defaults()
        if db_group:
            self.populate_from(db_group)


    def update_defaults(self):
        self.props_defaults = self.db.get_settings()['defaults']
        for key, val in self.props_defaults.items():
            assert 'type' in val
            assert 'desc' in val
            
            val_type = py_type_from_db_type(val['type'])

            if val['type'] == 'int' or val['type'] == 'float':
                assert 'min' in val
                assert 'max' in val
                assert 'step' in val
            val['type'] = val_type


    def clear(self):
        self.name = ""
        self.tests = []
        self.description = ""
        self.db_group = None
        self.duration = None


    def populate_from(self, db_group):
        self.db_group = db_group
        self.name = db_group.name
        self.description = db_group.desc

        self.tests = db_group.get_tests()

        for test in self.tests:
            test.load_properties()

        self.duration = db_group.get_duration()
        self.passed = False


    def updated_db(self):
        if self.db_group:
            self.db_group.update(self.name, self.description,
                                 self.tests)
        else:
            self.db.add_group(self.name, self.description, self.tests)


    def add_tests_results(self, results):

        to_reduce = [ pass_fail for pass_fail in \
                      [ result[0].values() \
                          for result in \
                             results.values() ] ]

        self.passed = bool(min(reduce(lambda a, b: a + b, to_reduce))) \
                      if len(to_reduce) else False

        self.db_group.add_tests_results(results, self.tests)

    def override_tests_properties(self, overrides):
        for test in self.tests:
            for prop in overrides:
                test.pending_properties[prop] = overrides[prop]

    def get_unset(self):
        r = []
        for test in self.tests:
            props = test.pending_properties
            p = []
            for key, value in props.items():
                if value is None:
                    p += [ key ]
            if p:
                r += [ (test, p) ]
        return r
