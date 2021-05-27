LIBDEVTANKROOT := ../../..
OUTDIR := output

default: $(OUTDIR)/bin/adj_pwr.sh

include $(LIBDEVTANKROOT)/libhw/Makefile.libhw

ADJ_PWR_CFLAGS := $(CFLAGS) -D_GNU_SOURCE -std=gnu11 -Wall -Werror -MMD -MP -Wall $(LIBDEVTANK_INCLUDES)


$(OUTDIR)/build/adj_pwr/main.o : main.c
	mkdir -p `dirname $@`
	$(CC) $(ADJ_PWR_CFLAGS) -c $< -o $@

$(OUTDIR)/bin/adj_pwr: $(LIBDEVTANK_DYN) $(OUTDIR)/build/adj_pwr/main.o
	mkdir -p `dirname $@`
	$(CC) $(LIBDEVTANKTESTS_CFLAGS) $(ADJ_PWR_LDFLAGS) $(LIBDEVTANK_LDFLAGS) $(OUTDIR)/build/adj_pwr/main.o -L$(OUTDIR)/lib/ -lhw -lbase -lyamlhelper -o $@

include $(LIBDEVTANKROOT)/Makefile.post
