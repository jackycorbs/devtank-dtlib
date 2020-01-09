Introduction
============

This document is to describe the SQL structure used for storing tests
and their results.

There are many things Devtank would like to change and have
experimented with, but this document is for as they are in this
existing working system.


Overview
========

This schema is used for multiple SQL implementations, so only basic
types are used.

Currently actively supported is SQLite and MySQL, but there remains
legacy code for PostgreSQL and MsSQL that may be brought back to active
service when required.

Time is stored in Unix microseconds as a signed 64bit number, BIGINT.
This gives time range and precision for all foreseeable uses.

A lot of things exist in time windows for versioning.
These things have a "valid_from" time value that is set when the data is
created. They will also have a "valid_to" time value that is NULL until
there is a time the data is no longer current. This versioned data thus
requires a "now" time when querying. The "now" must be greater than or
equal to the "valid_from" and below the "valid_to" unless the "valid_to"
is NULL.

The database does not store files within the SQL database.
Files are stored in file stores. Files are immutable and not expected
to change.
At the time of writing the filstores can be sftp or smb protocol network
shared folders. When working with sftp and SQLite, it the sftp host is
"localhost" a shortcut is obviously made.

Devices are stored in a project specific table but with expected known
keys. Devices will always have a "serial_number" text field, and a "uid"
text field. "uid" is for discoverable identification, for example, on
a network device, this could be the MAC address. For simple projects
"uid" is also set to the serial number.

A test is reference to a file and argument to pass it.
A tests group is a collection of tests run in a particular order with
particular argument values.

A result is a pass/fail, duration and log files for a test in a tests
group for a device. Results are in a project specific table as it refers
to project device table, and could contain project specific data.

Results are children of tests group results (often called sessions).
A session has a time of tests, what tests group and a time of tests.
It may also have a reference to a client machine that run the tests
and a software version the client machine was running.


There is a generic value tree system. A value has a name, a parent and
can be text, int, real or refer to a file in a file store.


Value 1 is "version" and tells you the version of the schema in the
database. The client will refuse to connect to database where the
schema's version number is too low. Some features the client will query
the schema version before using. 

These are the value standard trees

* "settings" - root for database settings values.
- "defaults" - default values for known arguments used by tests.
- "dev_table" - name of project specific device table.
- "dev_results_table" - name of project version of results table.
- "dev_results_table_key" - name of key in project results linking to
  project devices.
- "dev_results_values_table" - name of project results values table.
* "tests_properties" - values used for arguments of tests.
* "results_values" - values recorded during testing.
