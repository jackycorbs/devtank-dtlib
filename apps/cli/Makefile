OUTDIR := output
LIBDEVTANKROOT:=../..

EXAMPLE_TESTER_PY_MODS := \
    $(OUTDIR)/build/dt_db_base \
    $(OUTDIR)/build/dt_cli_base \
    $(OUTDIR)/build/example_lib \
    $(OUTDIR)/build/resources

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

$(OUTDIR)/build/resources: resources/* $(LIBDEVTANKROOT)/pylibapps/resources/* Makefile
	mkdir -p $(OUTDIR)/build
	mkdir -p $(OUTDIR)/resources
	cp -v resources/*   $(OUTDIR)/resources/
	cp -v $(LIBDEVTANKROOT)/pylibapps/resources/*  $(OUTDIR)/resources/
	touch $(OUTDIR)/build/resources

COVERAGERUN=PYTHONPATH=output/lib LD_LIBRARY_PATH=output/lib python3-coverage run ./output/bin/example_tester_cli.py --config /tmp/dt_test.yaml

coverage: default
	rm -rf /tmp/dt_test.db /tmp/dt_test_files
	echo "{ type: sqlite, filename: /tmp/dt_test.db, db_files: /tmp/dt_test_files }" > /tmp/dt_test.yaml
	$(COVERAGERUN) update_tests tests/groups.yaml
	$(COVERAGERUN) fake_dev 04
	$(COVERAGERUN) run_group "Example Group" 04
	python3-coverage html
	sensible-browser htmlcov/index.html

include $(LIBDEVTANKROOT)/pylibapps/Makefile.pylibapps

include $(LIBDEVTANKROOT)/libbase/Makefile.libbase

include $(LIBDEVTANKROOT)/Makefile.post
