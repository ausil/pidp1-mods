# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC= -I../../src/common -I../../src/pdp1 -I.. -I../Lib
CFLAGS += $(INC) -fPIC

%.o:%.c ../iotHandler.h ../../src/pdp1/dynamicIots.h ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h ../Lib/iotLogger.h ../../src/pdp1/configuration.h type340emu.h
	$(CC) $(CFLAGS) -c $< -o $@

%.so:%.o type340emu.o ../Lib/iotLogger.o
	$(CC) $(CFLAGS) -shared $< ../Lib/iotLogger.o type340emu.o -o $@

all: IOT_15.so IOT_16.so IOT_17.so

install: all
	cp *.so ..

IOT_15.o: IOT_15.c ../iotHandler.h ../../src/pdp1/dynamicIots.h ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h ../Lib/iotLogger.h ../../src/pdp1/configuration.h type340emu.h type340emu.o
	$(CC) $(CFLAGS) -c IOT_15.c

IOT_16.o: IOT_16.c ../iotHandler.h ../../src/pdp1/dynamicIots.h ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h
	$(CC) $(CFLAGS) -c IOT_16.c

IOT_17.o: IOT_17.c ../iotHandler.h ../../src/pdp1/dynamicIots.h ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h
	$(CC) $(CFLAGS) -c IOT_17.c

type340emu.o: type340emu.c ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h ../Lib/iotLogger.h ../../src/pdp1/highSpeedChannels.h ../../src/pdp1/display.h ../../src/pdp1/configuration.h type340emu.h
	$(CC) $(CFLAGS) -c type340emu.c

clean:
	@rm *.o *.so 2>/dev/null || true

# Lib's objects are built by its own Makefile, which knows their headers.
../Lib/%.o: FORCE
	$(MAKE) -C ../Lib $*.o

FORCE:
