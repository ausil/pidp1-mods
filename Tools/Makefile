# Builds the tools that have no directory of their own, and drives the tool directories
# that install.sh wants built here. install.sh (via install/build-all.sh) calls "make install".
#
# 2022 adb6037 deleted the previous version of this file but left install.sh calling
# "make -C Tools install", so pdp1audio, mactoam1 and disassemble silently stopped being
# built and installed. Paths are corrected for the current tree layout.

CC=gcc -O2 -Wall
INC=-I../src/common

all: pdp1audio tools

pdp1audio: pdp1audio.c ../src/common/common.c
	$(CC) $(INC) $^ -o $@

tools:
	cd MtoA; $(MAKE) install
	cd Disassembler; $(MAKE) install

install: pdp1audio
	cp pdp1audio ../bin
	strip ../bin/pdp1audio

clean:
	rm -f *.o pdp1audio
