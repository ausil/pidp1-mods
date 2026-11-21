# Shared code.
# Each tool compiles what it uses from here from its own Makefile,
# so the tools need nothing built here
# "make" here compiles every file just as a check.
# The link client needs the emulator's ad1proto.h, the wire format.

# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build. See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC=-I../../src/pdp1
files := $(wildcard *.c)

%.o:%.c
	$(CC) $(CFLAGS) $(INC) -c $< -o $@

all: $(files:.c=.o)

clean:
	@rm -f *.o >/dev/null 2>&1
