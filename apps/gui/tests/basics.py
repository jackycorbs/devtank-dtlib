'''Example test script.

Basic checks of device before processed

Input Variables:

  args    - arguments dictionary given to demo tester that may be used to
             changed nature of test.
  dev     - Example device under test
  name    - Name of test being run.
  results - Results map of all tests.

Test Specific Arguments:
  args["hw_rev"] - hardware revision to expect

'''

from example_lib import CHECK_DESCS

expected_hw_rev = args["hw_rev"]
expected_mV = args["expected_mV"]
expected_mA = args["expected_mA"]




output_good("Welcome")

output_normal("Reading device 3.3V power rail.")
mV = dev.read_3v3_rail()
store_value("V3.3 power rail mV", mV)
threshold_check(mV, expected_mV, 90, "mV",  CHECK_DESCS.POWER_RAIL_3V3)

output_normal("Checking device current draw.")
mA = dev.read_current()
store_value("mA draw", mA)
threshold_check(mA, expected_mA, 10, "mA", CHECK_DESCS.POWER_RAIL_CURRENT)

output_normal("Read hardware revision from device pull ups.")
hw_rev = dev.read_revision()
store_value("HW Rev", hw_rev)
exact_check(hw_rev, expected_hw_rev, CHECK_DESCS.HW_REV)
