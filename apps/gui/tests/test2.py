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

test_var =  args["my_test_str"]

output_normal("Current UUID : " + dev.uuid)

output_normal("Arg : %s" % args["my_test_str"])

exact_check('"%s"' % test_var, '"%s"' % dev.read_serial(), "Fake Serial read.") 
threshold_check(3.4, 3.3, 0.2, "V", "Fake voltage check")

store_value("Test String", "hello there")
store_value("Test Int", 4)
store_value("Test Float", 3.5)
