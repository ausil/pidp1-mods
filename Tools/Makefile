# Builds the tools that have no directory of their own, and drives the tool directories
# that install.sh wants built here. install.sh (via install/build-all.sh) calls "make install".
#
# 2022 adb6037 deleted the previous version of this file but left install.sh calling
# "make -C Tools install", so pdp1audio, mactoam1 and disassemble silently stopped being
# built and installed. Paths are corrected for the current tree layout.

# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC=-I../src/common
CFLAGS += $(INC)

all: pdp1audio tools

pdp1audio: pdp1audio.c ../src/common/common.c
	$(CC) $(CFLAGS) $^ -o $@

tools:
	cd MtoA; $(MAKE) install
	cd Disassembler; $(MAKE) install

install: pdp1audio
	cp pdp1audio ../bin
# RPM builds keep the symbols for find-debuginfo(): strip is a checkout-time thing.
ifndef RPM_BUILD_ROOT
	strip ../bin/pdp1audio
endif

clean:
	rm -f *.o pdp1audio
