

from dt_db_base import basic_test_error_base

class Example_Error(basic_test_error_base):
    pass


class EXAMPLE_ERRORS:
    POWER_RAIL_3V3         = Example_Error(0x0001, "3.3V Power rail check")
    POWER_RAIL_CURRENT     = Example_Error(0x0002, "Power draw check")
    HW_REV                 = Example_Error(0x0003, "Expect Hardware revision")
