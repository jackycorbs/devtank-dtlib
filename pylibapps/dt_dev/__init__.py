import sys
if sys.version_info[0] < 3:
    from dev_run import dev_run_dev_on_file
else:
    from . import dev_run
    dev_run_dev_on_file = dev_run.dev_run_dev_on_file
