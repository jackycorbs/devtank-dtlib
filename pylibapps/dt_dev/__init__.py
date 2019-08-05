import sys
if sys.version_info[0] < 3:
    from dev_run import dev_run_dev_on_file
    from db_process import as_human_time, db_process_t, obj_valid_at
    from merger import merger_t
else:
    from . import dev_run, db_process, merger
    dev_run_dev_on_file = dev_run.dev_run_dev_on_file
    merger_t = merger.merger_t
    as_human_time = db_process.as_human_time
    db_process_t = db_process.db_process_t
    obj_valid_at = db_process.obj_valid_at

