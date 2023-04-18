

from dt_db_base import basic_test_desc


# Example of custom error text based on values
class power_draw_test_desc(basic_test_desc):
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


class CHECK_DESCS:
    POWER_RAIL_3V3     = basic_test_desc(0x0001, ("Expected voltage reading", "Unexpected voltage reading"))
    POWER_RAIL_CURRENT = power_draw_test_desc(0x0002, "Power draw")
    HW_REV             = basic_test_desc(0x0003, ("Supported Hardware revision", "Unsupported Hardware revision"))
    FIRMWARE_HW_ID     = basic_test_desc(0x0004, "HW ID read from firmware.")
    FIRMWARE_PROGRAM   = basic_test_desc(0x0005, ("Programmed firmware", "Failed to program firmware"))
    FIRMWARE_BOOT      = basic_test_desc(0x0006, ("Firmware booted", "Firmware not booted"))

