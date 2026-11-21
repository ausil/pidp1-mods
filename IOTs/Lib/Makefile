# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile. -fPIC: these objects link into every plugin.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC= -I../../src/common -I../../src/pdp1 -I.. -I../Lib
CFLAGS += $(INC) -fPIC

install: iotLogger.o asciitoflex.o flextoascii.o filenames.o display.o writeBehind.o

iotLogger.o: iotLogger.c iotLogger.h
	$(CC) $(CFLAGS) -c iotLogger.c

flextoascii.o: flextoascii.c flexlib.h
	$(CC) $(CFLAGS) -c flextoascii.c

asciitoflex.o: asciitoflex.c flexlib.h
	$(CC) $(CFLAGS) -c asciitoflex.c

filenames.o: filenames.c ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h
	$(CC) $(CFLAGS) -c filenames.c

display.o: display.c
	$(CC) $(CFLAGS) -c display.c

# The drum's and the microtape's write-behind queue (27-Sep-2026).
writeBehind.o: writeBehind.c writeBehind.h
	$(CC) $(CFLAGS) -c writeBehind.c

clean:
	@rm *.o 2>/dev/null || true
