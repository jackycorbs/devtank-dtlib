import datetime

from dt_db_base import default_run_group_manager
from dt_gui_base import base_run_context



class _RunContext(base_run_context):
    def __init__(self, context):
        base_run_context.__init__(self, context, default_run_group_manager)
        context.view_objs["RunGroupViewObj"] = self

    def set_run_ready(self):
        self.run_group_man.readonly = False

    def on_cancel(self):
        was_live = self.run_group_man.live
        base_run_context.on_cancel(self)
        if not was_live:
            self.run_group_man.clean_files()

    def on_ok(self):
        base_run_context.on_ok(self)
        self.run_group_man.clean_files()

    def on_redo(self):
        base_run_context.on_redo(self)
        self.run_group_man.clean_files()


def open_run_group(context):

    global _run_context

    _run_context.set_run_ready()

    context.push_view()
    context.change_view("RunGroupViewObj")

    _run_context.run_lab.set_text(context.tests_group.name)


def open_ran_group(context, session):

    global _run_context

    _run_context.load_session(session)

    context.push_view()
    context.change_view("RunGroupViewObj")

    stamp = datetime.datetime.fromtimestamp(session.time_of_tests)

    _run_context.run_lab.set_text('"%s"\n@ %s' % \
                                  (context.tests_group.name, str(stamp)))



def init_run_group(context):

    builder = context.builder

    global _run_context

    _run_context = _RunContext(context)
