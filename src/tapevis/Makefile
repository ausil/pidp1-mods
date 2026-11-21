# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
CFLAGS += -I../common

# Every file tapevis.c and common.c include, from gcc -MM -I../common tapevis.c ../common/common.c.
DEPS = ../common/common.h ../common/args.h

all: tapevis

tapevis: tapevis.c ../common/common.c $(DEPS)
	$(CC) $(CFLAGS) -o $@ tapevis.c ../common/common.c `sdl2-config --cflags --libs`
