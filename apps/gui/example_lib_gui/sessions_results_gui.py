from __future__ import print_function, absolute_import

import sys
from dt_gui_base import base_session_results_singlton



class _session_results_singlton(base_session_results_singlton):
    def __init__(self, context):
        base_session_results_singlton.__init__(self, context)

    def _on_open_ran_view(self, session):
        from .group_run_gui import open_ran_group

        open_ran_group(self.context, session)


_session_results = None


def open_tests_sessions_results(context):
    global _session_results
    _session_results.open()

def open_dev_tests_sessions_results(context, db_dev):
    global _session_results
    assert db_dev
    _session_results.open(db_dev)

def init_tests_sessions_results(context):
    global _session_results
    _session_results = _session_results_singlton(context)
