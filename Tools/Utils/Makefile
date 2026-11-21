# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
CFLAGS += -I../../src/common

all: mtp fstool asr33tape

install: mtp fstool asr33tape
	cp mtp ../../bin/mtp
	strip ../../bin/mtp
	cp fstool ../../bin/fstool
	strip ../../bin/fstool
	cp asr33tape ../../bin/asr33tape
	strip ../../bin/asr33tape

mtp: mtp.c
	$(CC) $(CFLAGS) mtp.c -o mtp

fstool: fstool.c
	$(CC) $(CFLAGS) fstool.c -o fstool

asr33tape: asr33tape.c
	$(CC) $(CFLAGS) asr33tape.c -o asr33tape

clean:
	@rm mtp fstool asr33tape *.o 2>/dev/null || true
