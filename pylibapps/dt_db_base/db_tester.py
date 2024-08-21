class db_tester_machine(object):
    def __init__(self,
                 db,
                 machine_id,
                 mac,
                 hostname):
        self.db       = db
        self.id       = machine_id
        self.mac      = mac.rstrip()
        self.hostname = hostname

    @staticmethod
    def get_all_machines(db):
        cmd = db.sql.get_all_machines()
        rows = db.db.query(cmd)
        return [ db_tester_machine(db, *row) for row in rows ]

    def get_sessions_count(self):
        cmd = self.db.sql.get_machine_sessions_count(self.id)
        row = self.db.db.query_one(cmd)
        if not row:
            return 0
        return row[0]

    def get_sessions(self, offset, count):
        from .db_tests import test_group_sessions
        cmd = self.db.sql.get_machine_sessions(self.id, offset, count)
        rows = self.db.db.query(cmd)
        r = []
        for row in rows:
            group_id = row[0]
            group = self.db.get_group_by_id(group_id)
            r += [ test_group_sessions(group, self.db, *row[1:]) ]
        return r

    @staticmethod
    def get_by_id(db, machine_id):
        if db.version < 4 or machine_id is None:
            return None

        cmd = db.sql.get_machine_by_id(machine_id)
        row = db.db.query_one(cmd)
        if not row:
            return None
        return db_tester_machine(db, *row)

    @staticmethod
    def get(db, mac, hostname):
        if db.version < 4:
            return None

        cmd = db.sql.get_machine(mac, hostname)
        row = db.db.query_one(cmd)
        if not row:
            return None
        return db_tester_machine(db, *row)

    @staticmethod
    def get_own_machine(db):
        if db.version < 4:
            return None
        try:
            own_mac=None
            with open("/proc/net/route") as f:
                for line in f:
                    parts = line.split()
                    if parts[1] == "00000000":
                        with open("/sys/class/net/%s/address" % parts[0]) as f2:
                            own_mac = f2.readline()
                            break
            if own_mac is None:
                # No default route, so just take first network device.
                print("Warning: Machine has no default route.")
                with open("/proc/net/route") as f:
                    for line in f:
                        parts = line.split()
                        if parts[1] != "Destination":
                            with open("/sys/class/net/%s/address" % parts[0]) as f2:
                                own_mac = f2.readline()
                                break
            if own_mac is None:
                print("Warning: Unable to find a MAC address for machine.")
                return None
        except:
            # The machine doesn't have procfs or sysfs setup right.
            return None

        own_hostname=None
        with open("/etc/hostname") as f:
            own_hostname = f.readline()

        own_mac = own_mac.strip()
        own_hostname = own_hostname.strip()

        machine = db_tester_machine.get(db, own_mac, own_hostname)
        if machine:
            return machine

        cmd = db.sql.add_machine(own_mac, own_hostname)
        machine_id = db.db.insert(cmd)
        return db_tester_machine.get_by_id(db, machine_id)
