# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile. (This file's -O0 -g was the old -O0 -g debugging
# default; the environment now decides optimization.)
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra

# drumlist compiles ovlload's .ovl reader straight in, as ovlload does, so that no
# object file is left in either directory.
UTILLIBS=../UtilLibs
CFLAGS += -I../../src/common -I$(UTILLIBS)

all: drumupdater drumlist

install: drumupdater drumlist
	cp drumupdater ../../bin
	cp drumlist ../../bin
	strip ../../bin/drumupdater
	strip ../../bin/drumlist

drumupdater: drumupdater.c
	$(CC) $(CFLAGS) drumupdater.c -o drumupdater

drumlist: drumlist.c $(UTILLIBS)/ovlfile.c $(UTILLIBS)/ovlfile.h
	$(CC) $(CFLAGS) drumlist.c $(UTILLIBS)/ovlfile.c -o drumlist

clean:
	@rm *.o drumupdater drumlist 2>/dev/null || true
