OUTDIR := output
LIBDEVTANKROOT:=../..

EXAMPLE_TESTER_PY_MODS := \
    $(OUTDIR)/build/dt_db_base \
    $(OUTDIR)/build/dt_gui_base \
    $(OUTDIR)/build/example_lib \
    $(OUTDIR)/build/example_lib_gui \
    $(OUTDIR)/build/resources

default: $(OUTDIR)/bin/example_tester_gui.sh

$(OUTDIR)/bin/example_tester_gui.sh: $(OUTDIR)/bin/example_tester_gui.py Makefile
	mkdir -p $(OUTDIR)/bin
	$(LIBDEVTANKROOT)/create_run_script.sh $(OUTDIR)/bin/example_tester_gui.py $(OUTDIR)/bin/example_tester_gui.sh

$(OUTDIR)/bin/example_tester_gui.py: example_tester_gui.py $(EXAMPLE_TESTER_PY_MODS) Makefile
	mkdir -p $(OUTDIR)/bin
	cp example_tester_gui.py $(OUTDIR)/bin/example_tester_gui.py
	chmod +x $(OUTDIR)/bin/example_tester_gui.py

$(OUTDIR)/build/example_lib : example_lib/*.py Makefile $(OUTDIR)/lib/libbase.so
	mkdir -p $(OUTDIR)/build
	mkdir -p $(OUTDIR)/lib/example_lib
	cp -v example_lib/*.py $(OUTDIR)/lib/example_lib/
	touch $(OUTDIR)/build/example_lib

$(OUTDIR)/build/example_lib_gui : example_lib_gui/*.py Makefile
	mkdir -p $(OUTDIR)/build
	mkdir -p $(OUTDIR)/lib/example_lib_gui
	cp -v example_lib_gui/*.py $(OUTDIR)/lib/example_lib_gui/
	touch $(OUTDIR)/build/example_lib_gui

$(OUTDIR)/build/resources: resources/* $(LIBDEVTANKROOT)/pylibapps/resources/* Makefile
	mkdir -p $(OUTDIR)/build
	mkdir -p $(OUTDIR)/resources
	cp -v resources/*   $(OUTDIR)/resources/
	cp -v $(LIBDEVTANKROOT)/pylibapps/resources/*  $(OUTDIR)/resources/
	touch $(OUTDIR)/build/resources

local_db_push:
	DB_OLD=`ls -1d old_db.* | wc -l`; \
	mkdir old_db.$$DB_OLD; \
	mv test.db db_files old_db.$$DB_OLD; \
	rm -rf files_cache test.db-journal

local_db_pop:
	DB_NAME=`ls -1d old_db.* | tail -n 1`; \
	mv $$DB_NAME/* ./ ; \
	rmdir $$DB_NAME ; \
	rm -rf files_cache test.db-journal; \
	mkdir files_cache

local_db_clean:
	rm -rf files_cache test.db test.db-journal db_files

coverage: default
	python3-coverage erase
	PYTHONPATH=output/lib LD_LIBRARY_PATH=output/lib python3-coverage run --include "output/*" ./output/bin/example_tester_gui.py --desktop
	python3-coverage html
	sensible-browser htmlcov/index.html

include $(LIBDEVTANKROOT)/pylibapps/Makefile.pylibapps

include $(LIBDEVTANKROOT)/libbase/Makefile.libbase

include $(LIBDEVTANKROOT)/Makefile.post
