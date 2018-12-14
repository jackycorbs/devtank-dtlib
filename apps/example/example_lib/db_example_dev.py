from dt_db_base import db_child


class db_example_dev(db_child):
    def __init__(self,
                 db,
                 serial_number,
                 dev_db_id,
                 uuid):
        db_child.__init__(self, db, db_id=dev_db_id, db_serial=serial_number, db_extra=uuid)
        self.test_results = { "Pass": [], "Fail": [] }
        self.uuid = uuid

    @staticmethod
    def get_by_serial(db, serial_number):
        return db_child._get_by_serial(db, db_example_dev,
                                        db.sql.get_example_dev_by_serial,
                                        serial_number)

    @staticmethod
    def get_by_id(db, dev_id):
        return db_child._get_by_id(db, db_example_dev,
                                    db.sql.get_example_dev_by_id,
                                    dev_id)

    @staticmethod
    def get_by_uuid(db, uuid):
        return db_child._get_by_extra(db, db_example_dev,
                                    db.sql.get_example_dev_by_uid,
                                    uuid)

    @staticmethod
    def create(db, serial_number, uuid):
        cmd = db.sql.create_dev(serial_number, uuid)
        dev_id = db.db.insert(cmd)
        return db_example_dev.get_by_id(db, dev_id)

    def update_latest_results(self):
        cmd = self.db.sql.dev_latest_results(self.id)
        rows = self.db.db.query(cmd)
        r = { "Pass": [], "Fail": [] }
        for row in rows:
            pass_fail = "Pass" if row[1] else "Fail"
            r[pass_fail] += [{'group_id'        : row[2],
                              'group_name'      : row[3],
                              'session_id'      : row[4],
                              'result_id'       : row[0]}]
        self.test_results = r

    def get_latest_results(self):
        if not len(self.test_results['Pass']) or \
           not len(self.test_results['Fail']):
            self.update_latest_results()
        return self.test_results
