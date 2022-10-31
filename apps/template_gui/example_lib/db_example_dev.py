from dt_db_base import db_base_dev


class db_example_dev(db_base_dev):
    def __init__(self,
                 db,
                 serial_number,
                 dev_db_id,
                 uuid):
        db_base_dev.__init__(self, db, serial_number, dev_db_id, uuid)

    @staticmethod
    def get_by_serial(db, serial_number):
        return db_base_dev._get_by_serial(db_example_dev, db,
                                              serial_number)

    @staticmethod
    def get_by_id(db, dev_id):
        return db_base_dev._get_by_id(db_example_dev, db, dev_id)

    @staticmethod
    def get_by_uuid(db, uuid):
        return db_base_dev._get_by_uuid(db_example_dev, db, uuid)

    @staticmethod
    def create(db, serial_number, uuid):
        cmd = db.sql.create_dev(serial_number, uuid)
        dev_id = db.db.insert(cmd)
        return db_example_dev.get_by_id(db, dev_id)
