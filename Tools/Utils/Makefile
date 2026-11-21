# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
CFLAGS += -I../../src/common

all: mtp fstool asr33tape

install: mtp fstool asr33tape
	cp mtp ../../bin/mtp
# RPM builds keep the symbols for find-debuginfo(): strip is a checkout-time thing.
ifndef RPM_BUILD_ROOT
	strip ../../bin/mtp
endif
	cp fstool ../../bin/fstool
# RPM builds keep the symbols for find-debuginfo(): strip is a checkout-time thing.
ifndef RPM_BUILD_ROOT
	strip ../../bin/fstool
endif
	cp asr33tape ../../bin/asr33tape
# RPM builds keep the symbols for find-debuginfo(): strip is a checkout-time thing.
ifndef RPM_BUILD_ROOT
	strip ../../bin/asr33tape
endif

mtp: mtp.c
	$(CC) $(CFLAGS) mtp.c -o mtp

fstool: fstool.c
	$(CC) $(CFLAGS) fstool.c -o fstool

asr33tape: asr33tape.c
	$(CC) $(CFLAGS) asr33tape.c -o asr33tape

clean:
	@rm mtp fstool asr33tape *.o 2>/dev/null || true
