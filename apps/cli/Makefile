OUTDIR := output
LIBDEVTANKROOT:=../..

EXAMPLE_TESTER_PY_MODS := \
    $(OUTDIR)/build/dt_db_base \
    $(OUTDIR)/build/dt_cli_base \
    $(OUTDIR)/build/example_lib \

default: $(OUTDIR)/bin/example_tester_cli.sh

$(OUTDIR)/bin/example_tester_cli.sh: $(OUTDIR)/bin/example_tester_cli.py Makefile
	mkdir -p $(OUTDIR)/bin
	$(LIBDEVTANKROOT)/create_run_script.sh $(OUTDIR)/bin/example_tester_cli.py $(OUTDIR)/bin/example_tester_cli.sh

$(OUTDIR)/bin/example_tester_cli.py: example_tester_cli.py $(EXAMPLE_TESTER_PY_MODS) Makefile
	mkdir -p $(OUTDIR)/bin
	cp example_tester_cli.py $(OUTDIR)/bin/example_tester_cli.py
	chmod +x $(OUTDIR)/bin/example_tester_cli.py

$(OUTDIR)/build/example_lib : example_lib/*.py Makefile $(OUTDIR)/lib/libbase.so
	mkdir -p $(OUTDIR)/lib/example_lib
	cp -v example_lib/*.py $(OUTDIR)/lib/example_lib/
	touch $(OUTDIR)/build/example_lib


include $(LIBDEVTANKROOT)/pylibapps/Makefile.pylibapps

include $(LIBDEVTANKROOT)/libbase/Makefile.libbase

include $(LIBDEVTANKROOT)/Makefile.post
