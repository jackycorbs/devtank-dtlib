Devtank Production Tester Lib
=============================

This is a generic framework for making production testers.

Test scripts are written in Python and results are inserted into a SQL
database.


This code has grown sometimes under very rapid timelines and is used in
anger on multiple projects. There is much Devtank would like to do to
it, but for now, it does the job. It is "work in progress".

It runs on Debian based GNU/Linux (Ubuntu,Mint,etc)

To install the dependencies do:

    ./build_dep.sh

To run the GUI example co:

    cd apps/gui/
    make
    ./output/bin/example_tester_gui.sh --desktop

The serial number is free text. It needs entering twice as that is a
barcode check.

Agree the board (that doesn't exist as it's an example) is in the
fixture and then the tests for the board are run.

The tests are basically instant in this example.
You can click 'i' to see the text output of a test. Select
the "log" tab to see the more detailed information of a test.
Once the tests have completed, you can change which test is selected and
view the "output" and "log" of each.

It's all designed to be simple.


To be able to select and edit tests, add the "--super" argument.
