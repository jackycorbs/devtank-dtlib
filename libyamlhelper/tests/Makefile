LIBDEVTANKROOT := ../..
OUTDIR := output
CFLAGS := -O0 -g

default: tests

include $(LIBDEVTANKROOT)/Makefile.test_pre
include $(LIBDEVTANKROOT)/libyamlhelper/Makefile.libyamlhelper

include Makefile.tests

include $(LIBDEVTANKROOT)/Makefile.post
include $(LIBDEVTANKROOT)/Makefile.test_post
