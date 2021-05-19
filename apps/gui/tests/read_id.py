'''Example test script.

Update UUID of database version of device from hardware.

Input Variables:

  args    - arguments dictionary given to demo tester that may be used to
             changed nature of test.
  dev     - Example device under test
  name    - Name of test being run.
  results - Results map of all tests.

'''

output_normal("Original UUID : " + dev.uuid)

dev.update_uuid_from_hw()

output_normal("New UUID : " + dev.uuid)

output_bad("Device might be hot!")
