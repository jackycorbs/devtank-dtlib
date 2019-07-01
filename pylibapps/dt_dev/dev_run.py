from __future__ import print_function
import os
import sys
import glob

_ANSI_RED     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_DEFAULT = "\x1B[39m"

log_file = None
output_file = None
org_debug_print = None

def output_bad(msg):
    print(_ANSI_RED + msg + _ANSI_DEFAULT)
    if output_file:
        print(msg, file=output_file)
    if log_file:
        print("BAD OUTPUT: " + msg, file=log_file)

def output_good(msg):
    print(_ANSI_GREEN + msg + _ANSI_DEFAULT)
    if output_file:
        print(msg, file=output_file)
    if log_file:
        print("GOOD OUTPUT: " + msg, file=log_file)

def output_normal(msg):
    print(msg)
    if output_file:
        print(msg, file=output_file)
    if log_file:
        print("OUTPUT: " + msg, file=log_file)

def test_check(test_name, args, results, result, desc):
    if result:
        output_good("%s - passed" % desc)
    else:
        results[test_name] = False
        output_bad("%s - FAILED" % desc)
        if "exit_on_fail" in args and args["exit_on_fail"]:
            sys.exit(-1)

def threshold_check(test_name, args, results, sbj, ref, margin, unit, desc):
    test_check(test_name, args, results, abs(sbj - ref) <= margin, "%s %g%s == %g%s +/- %g" % (desc, sbj, unit, ref, unit, margin))

def exact_check(test_name, args, results, sbj ,ref, desc):
    test_check(test_name, args, results, sbj == ref, "%s (%u == %u) check" % (desc, sbj, ref))

def debug_print(msg):
    print(msg, file=log_file)
    if org_debug_print:
        org_debug_print(msg)


def dev_run_dev_on_file(dev, get_dbg_print, set_dbg_print, test_file, used_arg_num):
    global org_debug_print

    if get_dbg_print:
        org_debug_print = get_dbg_print()

    args = {}
    name = os.path.basename(test_file)
    results = {}

    if len(sys.argv) > used_arg_num:
        for n in range(used_arg_num, len(sys.argv), 2):
            next_n = n + 1
            if next_n < len(sys.argv):
                name = sys.argv[n]
                value = sys.argv[next_n]
                try:
                    if value.find(".") != -1:
                        value = float(value)
                    else:
                        value = int(value)
                except:
                    pass
                args[name] = value

    if test_file.find("*") != -1:
        tests = glob.glob(test_file)
        tests.sort()
    else:
        tests = [ test_file ]

    for test in tests:
        test_file = test

        if os.path.islink(test_file):
            test_file = os.readlink(test_file)

        name = os.path.basename(test_file)

        global log_file, output_file

        log_file    = open("/tmp/" + name + ".log", "w")
        output_file = open("/tmp/" + name + ".output", "w")

        if set_dbg_print:
            set_dbg_print(debug_print)

        print("\n===== %s =======\n" % name)

        results[name] = True

        test_exec_map = { 'args': args,
                          'dev': dev,
                          'name': name,
                          'results': results,
                          '__file__' : os.path.abspath(test_file),
                          'test_check': lambda a,b: test_check(name, args, results, a, b),
                          'output_normal' : output_normal,
                          'output_good' : output_good,
                          'output_bad' : output_bad,
                          'threshold_check' : lambda a,b,c,d,e: threshold_check(name, args, results, a, b, c, d, e),
                          'exact_check' : lambda a,b,c: exact_check(name, args, results, a, b, c)}

        exec(open(test_file).read(), test_exec_map)

        if set_dbg_print:
            set_dbg_print(org_debug_print)

    print("\n===== RESULTS =======\n")
    for name in results:
        if results[name]:
            print(_ANSI_GREEN + ("* - '%s' - passed" % name) + _ANSI_DEFAULT)
        else:
            print(_ANSI_RED + ("* - '%s' - FAILED" % name) + _ANSI_DEFAULT)
