# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build. See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra

all: docviewer

docviewer: docviewer.c
	$(CC) $(CFLAGS) -o docviewer docviewer.c

install: docviewer
	cp docviewer ../../bin/docviewer
	strip ../../bin/docviewer

clean:
	@rm docviewer 2>/dev/null || true
