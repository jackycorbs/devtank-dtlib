Devtank Production Tester Database Queries
==========================================

Please reference to the Schema document to diagest the many tables and
relationships before reading this document.



You will need to join multiple tables in queries for most things.


To queries from SQLite it only the time functions to go in and out of Unix time that needs to change.





Example of listing failure messages in the last day
===================================================


When a test fails, the text it failed with is recorded to the database in the values table.

In this example query we are going to get the time a test run was done, the machine it was on, the test group run and the test in that group that failed and finally the text of that failure.

The SQLite query is:


    SELECT datetime(time_of_tests / 1000000, 'unixepoch', 'localtime') AS test_time,
           tester_machines.mac AS tester, example_devs.serial_number AS device, test_groups.name AS group_name,
           test_group_entries.name AS test_name, `values`.value_text AS fail_text
    FROM example_dev_test_results
    JOIN test_group_entries ON test_group_entries.id = group_entry_id
    JOIN test_group_results ON test_group_results.id = example_dev_test_results.group_result_id
    JOIN test_groups ON test_groups.id = test_group_results.group_id
    JOIN example_devs ON example_devs.id = example_dev_id 
    JOIN tester_machines on tester_machines.id = tester_machine_id
    LEFT JOIN example_dev_test_results_values ON example_dev_test_results_values.test_result_id = example_dev_test_results.id
    LEFT JOIN `values` ON `values`.id = example_dev_test_results_values.value_id
    WHERE strftime('%s', 'now', '-1 day') * 1000000 > time_of_tests AND `values`.name LIKE 'SUB_FAIL%'
    ORDER BY test_time


Queries of the results start with the application specific device results table.
To this we join the test group entries to get the name of the tests in in the group and the test group results to get the test session's start time.
Next we want the name of the group so using the test group result table's group ID link in the test groups table.
We also want the serial of the device being tested, so we link in the devices table.
We also want the MAC of the tester used, so we link in the tester machines table.
We want the text of the failure from the values table so we need to first link the table linking results and values tables and then the values table itself.

We aren't interested in all recorded values during the test, only the "SUB_FAIL" kind as that's the name they are recorded under.
Also, we don't want all results ever as the database could be very big, so we just take results of session run in the last day.



Example of listing current test groups
======================================

Though we probably know the name of the test groups in the database, there may be multiple versions of each each with it's own set of results.

To get just name and ID of the current tests we can do:

    SELECT id, name FROM test_groups WHERE valid_to IS NULL


However, if we want all the versions of a test, called say, "Sunny Day", we could do:


    SELECT id,
       datetime(valid_from / 1000000, 'unixepoch', 'localtime') as valid_from,
       datetime(valid_to / 1000000, 'unixepoch', 'localtime') as valid_to
    FROM test_groups WHERE name="Sunny Day"


If found the ID, say 13, of a test group we know was bad, we can find the devices it was used with by doing:


   SELECT datetime(time_of_tests / 1000000, 'unixepoch', 'localtime') AS test_time,
          serial_number
   FROM test_group_results
   JOIN example_dev_test_results ON example_dev_test_results.group_result_id = test_group_results.id
   JOIN example_devs ON example_devs.id = example_dev_id
   WHERE test_group_results.group_id = 13
    

Knowing the specific group ID already, we don't need the test_groups table, we can just go striaght to the test_group_results with that.
With the test_group_results table we can then join the device results table example_dev_test_results table.
Finally we can then join the devices table to result from device ID to serial number. Or anything project specific in that version of the devices table.



Example of specific device history
==================================


Say we have a board/device of the serial we want to get the history of.
We could look it's results up. Here's a quick query to find the history of BOARD_66613.


   SELECT datetime(time_of_tests / 1000000, 'unixepoch', 'localtime') AS test_time,
          test_groups.name,
          test_group_entries.name,
          example_dev_test_results.pass_fail
   FROM example_devs
   JOIN example_dev_test_results ON example_dev_test_results.example_dev_id = example_devs.id
   JOIN test_group_results ON test_group_results.id = example_dev_test_results.group_result_id
   JOIN test_groups ON test_groups.id = test_group_results.group_id
   JOIN test_group_entries ON test_group_entries.id = example_dev_test_results.group_entry_id
   WHERE serial_number="BOARD_66613"

We start spinning up our query from the devices table.
We join to that all the device results.
So we have the test run times and test group ID, we link in the group results table.
To get test group name from the ID we link in the test group table.
To get the test names we link in the test groups entry table.

This gives us the names and times and pass or fail of the tests this board has had.



Example of test duration times
==============================

Some times test need aren't deterministic as there is waiting for external factors.
To find out what the average time taken by all the tests are we could simple do:


   SELECT test_groups.name AS group_name,
          test_group_entries.name AS test_name,
          AVG(example_dev_test_results.duration) / 1000000 AS seconds
   FROM example_dev_test_results
   JOIN test_group_results ON test_group_results.id = example_dev_test_results.group_result_id
   JOIN test_groups ON test_groups.id = test_group_results.group_id
   JOIN test_group_entries ON test_group_entries.id = example_dev_test_results.group_entry_id
   GROUP BY group_name, test_name

However, this may not be useful as it's the average over all time.
We'd be better asking for an average over a specific peroid of time. We could of course do that with a WHERE before the GROUP BY to frame the time we are interested in:

   WHERE time_of_tests > strftime('%s', '2004-01-01 13:00:00') * 1000000 AND time_of_tests < strftime('%s', '2034-01-01 13:00:00') * 1000000
