INC=-I../common -I../pdp1 -IPinctrl
LIBS=-lpthread -lm

# The tree-wide build convention: CC and CFLAGS come in from the environment
# (rpmbuild exports %optflags); the ?= defaults are for a bare source build;
# requirements are appended. See src/pdp1/Makefile for the full note.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
CFLAGS += $(INC) -Wno-unused-result

# Link the libgpiod backend when Pinctrl/ compiled it in (same pkg-config
# question as Pinctrl/Makefile asks; see the note there).
ifeq ($(shell pkg-config --exists libgpiod 2>/dev/null && echo 1),1)
LIBS += $(shell pkg-config --libs libgpiod)
endif

all: pinctrl newpanel

newpanel: pinctrl newpanel.o common.o configuration.o
	$(CC) $(CFLAGS) -o newpanel newpanel.o common.o configuration.o Pinctrl/*.o $(LIBS)

newpanel.o: newpanel.c
	$(CC) $(CFLAGS) -c newpanel.c

common.o: ../common/common.c
	$(CC) $(CFLAGS) -c ../common/common.c

configuration.o: ../pdp1/configuration.c
	$(CC) $(CFLAGS) -c ../pdp1/configuration.c

run: newpanel
	./newpanel

pinctrl:
	cd Pinctrl; $(MAKE)

clean:
	@rm newpanel *.o >/dev/null 2>&1 || true
	cd Pinctrl; $(MAKE) clean
