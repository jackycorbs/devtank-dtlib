'''Example test script.

Program device with given firmware

Input Variables:

  args    - arguments dictionary given to demo tester that may be used to
             changed nature of test.
  dev     - Example device under test
  name    - Name of test being run.
  results - Results map of all tests.

Test Specific Arguments:
  args["firmware"] - file of firmware to program device with
  args["serial"] - text expected from serial.

'''

firmware_file = args["firmware"]
expected_serial = args["serial"]
write_enable = args["write_enable"]

output_normal("Programming device.")
dev.write_enable = write_enable
dev.send_firmware(firmware_file)
dev.reset()

output_normal("Reading device serial for boot message.")
serial_data = dev.read_serial()
store_value("Serial Data", serial_data)
exact_check('"%s"' % expected_serial, '"%s"' % serial_data, "Serial welcome message")
