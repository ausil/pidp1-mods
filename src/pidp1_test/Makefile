# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC=-I../common
CFLAGS += $(INC)
LIBS=-lpthread -lm

all: pidp1_test

pidp1_test: main.c ../common/common.c
	$(CC) $(CFLAGS) -o $@ $^ $(LIBS)

clean:
	@rm -f pidp1_test 2>/dev/null || true

.PHONY: all clean
