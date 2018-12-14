
OUTDIR := output
LIBDEVTANKROOT:= .

default: doc

.PHONY: doc
doc: Doxyfile
	@ echo "======================"
	@ echo "BUILDING DOCUMENTATION"
	@ echo "======================"
	doxygen Doxyfile
	@ echo "================================"
	@ echo "Documentation at html/index.html"
	@ echo "================================"

.PHONY: cppcheck
cppcheck:
	cppcheck --enable=all $(LIBDEVTANK_INCLUDES) $(shell find $(LIBDEVTANKROOT)/lib*/src -type f -name '*.c')

include Makefile.post
