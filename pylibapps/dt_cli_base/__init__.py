import sys
if sys.version_info[0] < 3:
    from cli import generic_cmds, print_cmd_help, execute_cmd
else:
    from .cli import generic_cmds, print_cmd_help, execute_cmd
