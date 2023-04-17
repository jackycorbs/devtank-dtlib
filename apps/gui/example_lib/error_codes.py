

from dt_db_base import basic_test_error_base

class Example_Error(basic_test_error_base):
    pass

# Example of custom error text based on values
class Power_Draw_Error(basic_test_error_base):
    def get_text(self, passfail, args):
        if not passfail:
            sbj = args['sbj']
            ref = args['ref']
            margin = args['margin']

            if sbj > ref + margin:
                return f"Over current {sbj}mA > ({ref}mA + {margin}mA)"
            if sbj < ref - margin:
                return f"Under current {sbj}mA < ({ref}mA - {margin}mA)"
        return super().get_text(passfail, args)


class EXAMPLE_ERRORS:
    POWER_RAIL_3V3         = Example_Error(0x0001, ("Expected voltage reading", "Unexpected voltage reading"))
    POWER_RAIL_CURRENT     = Power_Draw_Error(0x0002, "Power draw")
    HW_REV                 = Example_Error(0x0003, ("Supported Hardware revision", "Unsupported Hardware revision"))
