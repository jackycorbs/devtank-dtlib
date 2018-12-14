'''Example test script.

This test programs the device with a provided executable.

Input Variables:

  args    - arguments dictionary given to pyaisg tester that may be used to
             changed nature of test.
  dev     - Example device under test
  name    - Name of test being run.
  results - Results map of all tests.

Test Specific Arguments:
  args["my_test_var"] - Test variable

'''

test_check (dev.uuid == "<unknown>", "UUID check" )
test_check (args["my_test_var"] == 4, "Variable check")
