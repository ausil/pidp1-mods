# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC=-I../common
CFLAGS += $(INC)
LIBS=-lpthread -lm

all: scanpf

scanpf: main.c ../common/common.c
	$(CC) $(CFLAGS) -o $@ $^ $(LIBS)

clean:
	@rm -f scanpf 2>/dev/null || true

.PHONY: all clean
