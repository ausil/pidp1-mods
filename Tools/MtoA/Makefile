# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build. See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra

all: mactoam1

install: mactoam1
	cp mactoam1 ../../bin/mactoam1
# RPM builds keep the symbols for find-debuginfo(): strip is a checkout-time thing.
ifndef RPM_BUILD_ROOT
	strip ../../bin/mactoam1
endif

mactoam1: mactoam1.o m1engine.o
	$(CC) $(CFLAGS) -o mactoam1 mactoam1.o m1engine.o

mactoam1.o: mactoam1.c m1engine.h
	$(CC) $(CFLAGS) -c mactoam1.c

m1engine.o: m1engine.c m1engine.h
	$(CC) $(CFLAGS) -c m1engine.c

clean:
	@rm mactoam1 *.o 2>/dev/null || true
