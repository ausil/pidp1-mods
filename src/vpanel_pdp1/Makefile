# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
CFLAGS += -I../common

# Every file main.c and common.c include, from gcc -MM -I../common main.c ../common/common.c.
DEPS = elements.inc art/panelart.inc art/pdp1art.inc ../common/common.h ../common/panel_pidp1.h

panel_pdp1: main.c ../common/common.c $(DEPS)
	$(CC) $(CFLAGS) -o $@ main.c ../common/common.c -lSDL2 -lSDL2_image
