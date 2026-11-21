# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build. See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra

all: docviewer

docviewer: docviewer.c
	$(CC) $(CFLAGS) -o docviewer docviewer.c

install: docviewer
	cp docviewer ../../bin/docviewer
# RPM builds keep the symbols for find-debuginfo(): strip is a checkout-time thing.
ifndef RPM_BUILD_ROOT
	strip ../../bin/docviewer
endif

clean:
	@rm docviewer 2>/dev/null || true
