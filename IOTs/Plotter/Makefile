# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC= -I../../src/common -I../../src/pdp1 -I.. -I../Lib
CFLAGS += $(INC) -fPIC
HDRS= ../iotHandler.h ../../src/pdp1/dynamicIots.h ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h ../../src/pdp1/configuration.h ../Lib/iotLogger.h ../Lib/writeBehind.h pngWrite.h

all: IOT_73.so

IOT_73.o: IOT_73.c $(HDRS)
	$(CC) $(CFLAGS) -c $< -o $@

pngWrite.o: pngWrite.c pngWrite.h
	$(CC) $(CFLAGS) -c $< -o $@

IOT_73.so: IOT_73.o pngWrite.o ../Lib/iotLogger.o ../Lib/writeBehind.o
	$(CC) $(CFLAGS) -shared IOT_73.o pngWrite.o ../Lib/iotLogger.o ../Lib/writeBehind.o -lz -lpthread -lm -o $@

install: all
	cp IOT_73.so ..

clean:
	@rm *.o *.so 2>/dev/null || true
