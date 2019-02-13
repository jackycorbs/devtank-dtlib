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

output_normal("Current UUID : " + dev.uuid)

output_good("I'm happy")
output_bad("I'm sad")
output_normal("I'm ok")

output_normal("Arg : %s" % args["my_test_str"])

