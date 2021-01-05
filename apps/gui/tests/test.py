'''Example test script.

This test programs the device with a provided executable.

Input Variables:

  args    - arguments dictionary given to demo tester that may be used to
             changed nature of test.
  dev     - Example device under test
  name    - Name of test being run.
  results - Results map of all tests.

Test Specific Arguments:
  args["my_test_var"] - Test variable

'''

output_normal("Original UUID : " + dev.uuid)
output_good("I'm happy")
output_bad("I'm sad")
test_check (args["my_test_var"] == 4, "Variable check")

dev.update_uuid_from_hw()

output_normal("New UUID : " + dev.uuid)
