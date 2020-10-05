from __future__ import print_function
import os
import sys
import time
import datetime
import traceback
import cPickle as pickle

import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib

from multiprocessing import Process

import c_base
import db_values

_IPC_CMD = "IPC_CMD:"



class base_run_group_context(object):
    def __init__(self, context, bus, last_end_time, stdout_out,
                 tmp_dir):
        tests_group = context.tests_group
        self.is_production = context.args['production']
        self.bus = bus
        self.tests = [(test.id, test.get_file_to_local(),
                       test.name,
                       test.run_arguments)\
                      for test in tests_group.tests]
        self.stdout_out = stdout_out
        self.test_group = tests_group.name
        self.devices = []
        self.last_end_time = last_end_time
        self.tmp_dir = tmp_dir

    def send_cmd(self, line):
        self.stdout_out.write("%s%s\n" % (_IPC_CMD, line))
        self.stdout_out.flush()

    def get_ready_devices(self, bus_con):
        raise Exception("Unimplemented")

    def stop_devices(self):
        raise Exception("Unimplemented")

    def finished(self, bus_con):
        self.send_cmd("FINISHED")

    def get_bus(self):
        return self.bus


class ForceExitException(Exception):
    """Raise an exception exit is forced."""
    pass


def _forced_exit():
    raise ForceExitException


def _test_check(lib_inf, test_name, args, results, result, desc):
    if result:
        lib_inf.output_good("%s - passed" % desc)
    else:
        results[test_name] = False
        lib_inf.output_bad("%s - FAILED" % desc)
        if "exit_on_fail" in args and args["exit_on_fail"]:
            _forced_exit()

def _threshold_check(lib_inf, test_name, args, results, sbj, ref, margin, unit, desc):
    _test_check(lib_inf, test_name, args, results, abs(sbj - ref) <= margin, "%s %g%s == %g%s +/- %g" % (desc, sbj, unit, ref, unit, margin))

def _exact_check(lib_inf, test_name, args, results, sbj ,ref, desc):
    _test_check(lib_inf, test_name, args, results, sbj == ref, "%s (%s == %s) check" % (desc, str(sbj), str(ref)))

def _store_value(test_context, n, v):
    data = pickle.dumps((n, v)).replace("\n","<NL>")
    test_context.send_cmd("STORE_VALUE " + data) # Base64 includes a newline



def _thread_test(test_context):
    bus = test_context.get_bus()

    lib_inf = test_context.__class__.lib_inf

    test_context.send_cmd("START_TESTS")

    lib_inf.output_normal("Starting test group: " + test_context.test_group)


    exec_map = {'exit': _forced_exit,
                'output_normal' : lib_inf.output_normal,
                'output_good' : lib_inf.output_good,
                'output_bad' : lib_inf.output_bad,
                'error_msg': lib_inf.error_msg,
                'warning_msg' : lib_inf.warning_msg,
                'info_msg' : lib_inf.info_msg,
                }

    with bus as bus_con:

        ready_devices = test_context.get_ready_devices(bus_con)

        full_stop=False

        for dev in ready_devices:
            results = {}

            dev_pass = True

            dev_uuid = dev.uuid.rstrip('\0')

            test_context.send_cmd("SELECT_DEV " + dev_uuid)

            for test in test_context.tests:

                test_id   = test[0]
                test_file = test[1]
                name      = test[2]
                args      = test[3]
                test_context.send_cmd("SELECT_TEST " + name)

                line = "Testing device: '%s' Test: '%s' of Group: '%s'"\
                        % (dev_uuid, name, test_context.test_group)

                stamp = datetime.datetime.utcnow()

                entry_name = "%s_%s_%s_%s" % (test_context.test_group,
                                              dev_uuid,
                                              name,
                                              str(stamp))
                entry_name = entry_name.replace('/', '_')

                log_path = os.path.join(test_context.tmp_dir,
                                        "%s.log" % entry_name)
                output_path = os.path.join(test_context.tmp_dir,
                                            "%s.output" % entry_name)

                test_context.send_cmd("START_OUTPUT %s" % output_path)
                test_context.send_cmd("START_LOGFILE %s" % log_path)

                duration = 0

                lib_inf.output_normal("=" * len(line))
                lib_inf.output_normal(line)
                lib_inf.output_normal("=" * len(line))

                results[name] = True

                try:
                    start_time = time.time()
                    lib_inf.enable_info_msgs(True)
                    test_exec_map = exec_map.copy()
                    test_exec_map.update({ 'args': args,
                                          'dev': dev,
                                          'name': name,
                                          'test_check': lambda a,b: _test_check(lib_inf, name, args, results, a, b),
                                          'threshold_check' : lambda a,b,c,d,e: _threshold_check(lib_inf, name, args, results, a, b, c, d, e),
                                          'exact_check' : lambda a,b,c: _exact_check(lib_inf, name, args, results, a, b, c),
                                          'results': results,
                                          'store_value' : lambda n, v : _store_value(test_context, n, v),
                                          '__file__' : os.path.abspath(test_file)})
                    execfile(test_file, test_exec_map)
                    lib_inf.enable_info_msgs(False)
                    duration = time.time() - start_time
                    post_dev_uuid = dev.uuid.rstrip('\0')
                    if dev_uuid != post_dev_uuid:
                        test_context.send_cmd("SET_UUID %s" % post_dev_uuid)
                        dev_uuid = post_dev_uuid
                    bus_con.poll_devices()
                except ForceExitException as e:
                    results[name] = False
                    lib_inf.output_bad("Forced Exit")
                    lib_inf.enable_info_msgs(False)
                except Exception as e:
                    results[name] = False
                    lib_inf.output_bad("Exception:")
                    for line in str(e).splitlines():
                        lib_inf.output_bad(line)
                    lib_inf.output_bad("Backtrace:")
                    for line in traceback.format_exc().splitlines():
                        lib_inf.output_bad(line)
                    lib_inf.enable_info_msgs(False)

                test_pass = results.get(name, False)

                dev_pass &= test_pass

                test_context.send_cmd("STATUS_TEST %s %G" % (str(bool(test_pass)), duration))

                if not test_pass and 'exit_on_fail' in args and args['exit_on_fail']:
                    full_stop = True
                    break

            test_context.send_cmd("STATUS_DEV %s" % str(bool(dev_pass)))

            if full_stop:
                break

        test_context.finished(bus_con)


_ANSI_ERR     = "\x1B[31m"
_ANSI_GREEN   = "\x1B[32m"
_ANSI_WARN    = "\x1B[33m"
_ANSI_DEFAULT = "\x1B[39m"



class base_run_group_manager(object):
    def __init__(self, context,
                 _run_group_context_class,
                 good_line = None,
                 bad_line = None,
                 normal_line = None,
                 info_line = None,
                 warning_line = None,
                 error_line = None,
                 cmds = None):
        self.process = None
        self.test_context = None
        self.last_end_time = 0
        self.context = context
        self._run_group_context_class = _run_group_context_class
        stdout_in, stdout_out = os.pipe()

        self.session_results = {}
        self.current_test = None
        self.current_device = None

        self.stdout_out = os.fdopen(stdout_out, "w", 0)
        self.stdout_in = os.fdopen(stdout_in, "r", 0)

        self.live = False
        self.readonly = False

        self.outfile = None
        self.logfile = None
        self.files = []

        no_op = lambda x: None

        self.good_line    = good_line if good_line else no_op
        self.bad_line     = bad_line if bad_line else no_op
        self.normal_line  = normal_line if normal_line else no_op

        self.info_line    = info_line if info_line else no_op
        self.warning_line = warning_line if warning_line else no_op
        self.error_line   = error_line if error_line else no_op

        self.has_new = False

        self.external_cmds = cmds if cmds else {}

        self.cmds = {"FINISHED":      lambda args:     self._finished(),
                     "SELECT_TEST":   lambda testfile: self._select_testfile(testfile),
                     "SELECT_DEV" :   lambda dev_uuid: self._select_dev(dev_uuid),
                     "START_OUTPUT":  lambda outfile:  self._start_outfile(outfile),
                     "START_LOGFILE": lambda logfile:  self._start_logfile(logfile),
                     "STATUS_TEST":   lambda args:     self._test_status(args),
                     "STATUS_DEV":    lambda passfail: self._dev_status(passfail == "True"),
                     "SET_UUID":      lambda new_uuid: self._dev_set_uuid(new_uuid),
                     "STORE_VALUE":   lambda data: self._store_value(data),
                     }

        GLib.io_add_watch(self.stdout_in,
                          GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR,
                          self._stdout_in_event)


    def _stdout_in_event(self, src, cond):
        line = self.stdout_in.readline()
        try:
            return self.process_line(line)
        except Exception as e:
            import traceback
            print("LINE PROCESS FAILED")
            traceback.print_exc()
            self.stop()
        ext_cmd = self.external_cmds.get("FINISHED",None)
        if ext_cmd:
            ext_cmd("")

    def _process_die_catch(self):
        if not self.process:
            return False
        if self.process.exitcode is None:
            return True
        if self.process.exitcode < 0:
            print("Process terminated.")
            self.live = False
            self._complete_stop()
            self._finished()
            return False
        return True

    def _finished(self):
        if self.outfile:
            self.outfile.close()
            self.outfile = None
        if self.logfile:
            self.logfile.close()
            self.logfile = None

    def _select_testfile(self, testfile):
        self.current_test = testfile
        self.session_results[self.current_device]['tests'][self.current_test] = {}

    def _select_dev(self, dev_uuid):
        self.current_device = dev_uuid
        self.session_results[self.current_device] = {'tests': {}}

    def _start_outfile(self, outfile):
        if self.outfile:
            self.outfile.close()
            self.outfile = None
        if len(outfile):
            self.outfile = open(outfile, "w")
            self.files += [outfile]
            self.session_results[self.current_device]['tests'][self.current_test]['outfile'] = outfile

    def _start_logfile(self, logfile):
        if self.logfile:
            self.logfile.close()
        self.logfile = None
        if len(logfile):
            self.logfile = open(logfile, "w")
            self.files += [logfile]
            self.session_results[self.current_device]['tests'][self.current_test]['logfile'] = logfile

    def _test_status(self, args):
        self.has_new = True
        args = args.split(' ')
        passfail = args[0]
        passfail = passfail == "True"
        duration = float(args[1])
        tests_results = self.session_results[self.current_device]['tests']
        if self.current_test in tests_results:
            results = tests_results[self.current_test]
            results['passfail'] = passfail
            results['duration'] = duration
        if self.outfile:
            self.outfile.close()
            self.outfile = None
        if self.logfile:
            self.logfile.close()
            self.logfile = None

    def _dev_status(self, passfail):
        self.session_results[self.current_device]['tests'][self.current_test]['passfail'] = passfail

    def _dev_set_uuid(self, new_uuid):
        dev_values = self.session_results.pop(self.current_device)
        if "old_uuid" not in dev_values:
            dev_values["old_uuid"] = self.current_device
        self.session_results[new_uuid] = dev_values
        for dev in self.context.devices:
            if dev.uuid.strip() == self.current_device:
                dev.uuid = new_uuid
        self.current_device = new_uuid

    def _store_value(self, data):
        data = pickle.loads(data.replace("<NL>","\n"))
        name = data[0]
        value = data[1]
        test_dict = self.session_results[self.current_device]['tests'][self.current_test]
        test_dict.setdefault("stored_values", {})
        test_dict["stored_values"][name] = value

    def process_line(self, line):
        if not self.live:
            if line.startswith(_IPC_CMD + "START_TESTS"):
                self.live = True
            return True
        if line.startswith(_IPC_CMD):
            line = line[len(_IPC_CMD):].strip()
            parts = line.split(' ')
            name = parts[0]
            opt = " ".join(parts[1:]) if len(parts) > 1 else None
            cb = self.cmds[name]
            cb(opt)
            if name in self.external_cmds:
                cb = self.external_cmds[name]
                cb(opt)
        else:
            ansi = None
            if len(line) > 22 and \
               line[2] == '/' and \
               line[5] == ' ' and \
               line[8] == ':' and \
               line[22] == '[':
                try:
                    #23 = len("25/01 10:51:47.241291 [")
                    s = line.index(' ', 24)
                    s += 1
                    e = line.index(':', s)
                    token = line[s:e]
                except:
                    token = ""
                ansi = None
                if token == "ERROR":
                    ansi = _ANSI_ERR
                    self.error_line(line)
                elif token == "WARN":
                    ansi = _ANSI_WARN
                    self.warning_line(line)
                else:
                    self.info_line(line)

                if self.logfile:
                    self.logfile.write(line)
                elif not self.readonly:
                    if ansi:
                        sys.stderr.write(ansi + line + _ANSI_DEFAULT)
                    else:
                        sys.stderr.write(line)
            else:
                if line.startswith("Good: "):
                    ansi = _ANSI_GREEN
                    self.good_line(line)
                elif line.startswith("BAD: "):
                    ansi = _ANSI_ERR
                    self.bad_line(line)
                else:
                    self.normal_line(line)

                if self.outfile:
                    self.outfile.write(line)
                elif not self.readonly:
                    if ansi:
                        sys.stderr.write(ansi + line + _ANSI_DEFAULT)
                    else:
                        sys.stderr.write(line)

        return True

    def start(self):
        lib_inf = self._run_group_context_class.lib_inf
        if self.process:
            return False
        bus = self.context.lock_bus()
        if not bus:
            return False

        try:
            self.readonly = False
            self.live = False
            self.has_new = False

            self.session_results = {}

            self.test_context = self._run_group_context_class(self.context, bus,
                                                              self.last_end_time,
                                                              self.stdout_out)
            lib_inf.set_output(self.stdout_out)
            lib_inf.set_log_file(self.stdout_out)

            self.process = Process(target=_thread_test,
                                  args=(self.test_context,))
            GLib.timeout_add_seconds(1, self._process_die_catch)
            self.process.start()
            return True

        except Exception as e:
            msg = "BAD: FAILED to start: %s\n" % str(e)
            lib_inf.output_bad("Backtrace:")
            for line in traceback.format_exc().splitlines():
                lib_inf.output_bad(line)
            self.stop()
            self.live = True
            self.process_line(msg)
            self.live = False
            self.context.release_bus()
            return False


    def wait_for_end(self):
        lib_inf = self._run_group_context_class.lib_inf
        self.live = False
        if self.process:
            self.process.join(4)
            self.process = None
            self.context.release_bus()

        lib_inf.set_log_file(None)
        lib_inf.set_output(None)

        self.last_end_time = time.time()
        self.readonly = True

    def _complete_stop(self):
        lib_inf = self._run_group_context_class.lib_inf
        lib_inf.set_log_file(None)
        lib_inf.set_output(None)
        self.test_context.stop_devices()
        self.process = None
        self.last_end_time = time.time()
        self.context.release_bus()

    def stop(self):
        self.live = False
        if self.process:
            self.process.terminate()
            # Give time for signal to get slave process.
            time.sleep(0.1)
            self._complete_stop()

        self._finished()

    def clean_files(self):
        for f in self.files:
            if os.path.exists(f):
                os.unlink(f)
        self.files = []
        self.has_new = False

    def load_files(self, dev, test):
        self.live = True
        if dev in self.session_results:
            dev_results = self.session_results[dev]['tests']
            if test in dev_results:
                values = dev_results[test]

                for k in [ 'outfile', 'logfile' ]:
                    f = values.get(k, None)
                    if f is None:
                        continue
                    if isinstance(f, int):
                        try:
                            local_file = self.context.db.get_file_to_local(f)
                            values[k] = local_file
                        except Exception as e:
                            self.process_line("BAD: Failed to load session: %s\n" % str(e))
                            self.live = False
                            local_file = None
                    else:
                        local_file = f
                    if local_file and os.path.exists(local_file):
                        with open(local_file, "r") as f:
                            for line in f:
                                self.process_line(line)
        self.live = False

    def load_session(self, session):
        self.has_new = False
        self.live = False
        self.readonly = True
        self.session_results = {}

        for uuid, dev_results in session.devices.items():
            r = {}
            for pass_fail, name, out_file_id, log_file_id in dev_results.results:
                r[name] = { 'passfail': pass_fail,
                            'outfile': out_file_id,
                            'logfile': log_file_id}
            self.session_results[uuid] = {'tests' : r}


    def is_pass(self, dev=None, test=None):
        if dev is None:
            if test is None:
                if not len(self.session_results):
                    return False
                for dev_tests in self.session_results.values():
                    dev_tests = dev_tests['tests']
                    for test_results in dev_tests.values():
                        if not test_results.get('passfail',False):
                            return False
                return True
            for uuid, dev_results in self.session_results.items():
                dev_results = dev_results['tests']
                if test not in dev_results:
                    return -1
                if not dev_results[test]['passfail']:
                    return False

            return True
        if test is None:
            if dev not in self.session_results:
                return -1
            r = [ results.get('passfail', False) \
                  for results in self.session_results[dev]['tests'].values()]
            return bool(min(r))
        if dev not in self.session_results:
            return -1
        dev_results = self.session_results[dev]['tests']
        if test not in dev_results:
            return -1
        return dev_results[test]['passfail']

    def submit(self):
        if self.has_new:
            self.context.tests_group.add_tests_results(self.session_results)
            self.clean_files()




class default_group_context(base_run_group_context):
    lib_inf = c_base

    def __init__(self, context, bus, last_end_time, stdout_out):
        tmp_dir="/tmp"
        base_run_group_context.__init__(self, context, bus, last_end_time, stdout_out, tmp_dir)
        self.devices = context.devices

    def get_ready_devices(self, bus_con):
        try:
            bus_con.ready_devices(self.devices)
            return bus_con.devices
        except Exception as e:
            print("Failed to get devices.")
            print("Backtrace:")
            for line in traceback.format_exc().splitlines():
                print(line)
            return []

    def stop_devices(self):
        # Tests have been killed, so open and close the bus to ensure it's closed.
        with self.bus as bus_con:
            pass


class default_run_group_manager(base_run_group_manager):
        def __init__(self, context,
                 good_line = None,
                 bad_line = None,
                 normal_line = None,
                 info_line = None,
                 warning_line = None,
                 error_line = None,
                 cmds = None):
            base_run_group_manager.__init__(self,
                                            context,
                                            default_group_context,
                                            good_line,
                                            bad_line,
                                            normal_line,
                                            info_line,
                                            warning_line,
                                            error_line,
                                            cmds)
