# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra

# make test writes everything the kit makes here, never into this directory
TESTDIR ?= /tmp/disasmtest

all: disassemble

install: disassemble
	cp disassemble ../../bin/disassemble
# RPM builds keep the symbols for find-debuginfo(): strip is a checkout-time thing.
ifndef RPM_BUILD_ROOT
	strip ../../bin/disassemble
endif

test: disassemble
	Tests/run_tests.sh -d disassemble -w $(TESTDIR)

disassemble: disassemble.o decode_instruction.o kloader.o am1loader.o binloader.o memloader.o
	$(CC) $(CFLAGS) -o disassemble disassemble.o decode_instruction.o kloader.o am1loader.o binloader.o memloader.o

disassemble.o: disassemble.c loader.h loaderdefs.h decode_instruction.h
	$(CC) $(CFLAGS) -c disassemble.c

decode_instruction.o: decode_instruction.c decode_instruction.h
	$(CC) $(CFLAGS) -c decode_instruction.c

kloader.o: kloader.c loader.h
	$(CC) $(CFLAGS) -c kloader.c

am1loader.o: am1loader.c loader.h
	$(CC) $(CFLAGS) -c am1loader.c

binloader.o: binloader.c loader.h
	$(CC) $(CFLAGS) -c binloader.c

memloader.o: memloader.c loader.h
	$(CC) $(CFLAGS) -c memloader.c

clean:
	@rm disassemble *.o 2>/dev/null || true

.PHONY: all install test clean
