Devtank Production Tester Lib
=============================

It is parts to make a GUI application that runs "test scripts" and
inserts results into a SQL database.

The "test scripts" use a binding to talk to a device.
The binding is different for each project, but certain things are
expected of this binding.

The binding is build round the concept of bus, bus connection and
devices.

The framework will open a bus and get a bus connection and then iterate
over the devices on the bus connection. It works like this because some
buses require power that you don't want applied all the time.

The framework is a mixture of C and Python, though binding can be pure
Python, or pure C exposed to Python (ctypes best used).

A "test" is a "test script" and it's known arguments/parameters.
The parameters/arguments have a name and a type, maybe a range and maybe
a default value.

Each "test" outputs two text files. A top level "output" file and a
detailed "log" file.

Each "test" is called with the predefined globals:

"dev"             : This is the device under test.
"args"            : Any adjustable argument of the test.
"name"            : The name the test is known as in the database.
"test_check"      : Arguments are (Boolean, check name)
"threshold_check" : Arguments are (Value, Reference Value, Threshold, Enginerring unit, Check name)
"exact_check"     : Arguments are (Value, Reference Value, Check name)
"output_normal"   : Message reported to "output" file.
"output_good"     : Message reported as good output and to "output" file.
"output_bad"      : Message reported as bad output and to "output" file.
"store_value"     : Add a named value to be stored in the database with the results.
"sleep"           : Sleep to use in tests, the wait will be logged in output. Can be overloaded with custom code.
"exit"            : Early exit the test. Default is a fail, but to exit early sucessfully, do exit(0)
"freeze_test"     : Pause the test in given position for hardware debug.


Tests are arranged into "test groups". These contain a list of tests and
the arguments they are to be called with.

Which tests are in a "test group" can change over time, but these
changes are tracked in the database.

Results are tracked to device and test within a test group. The results
have the "output" and "log" files as well as date, pass/fail, etc.

Results are collected in "sessions".

When you look back in time you will be able to see what test was run on
what device with what arguments and what the results were.

A device object is expected to have a database version of itself.

Please look in apps for example GUI and CLI.
