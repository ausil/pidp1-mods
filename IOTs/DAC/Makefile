# The D/A converters, IOT 71 and IOT 72 (FunStuff/Dacmusic). "make install"
# builds both and copies them to IOTs/, where the emulator loads them; the
# first IOT 71 or 72 a program gives loads them, with no restart. IOT 72 is
# IOT 71's alias for wavetable mode. room.h and edge.h are the room and the
# voicing, shared with FunStuff/Dacmusic/render's dacrender.

# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile. -shared, which this file's old CFLAGS carried, is now
# written on the link lines only.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC= -I../../src/common -I../../src/pdp1 -I.. -I../Lib
CFLAGS += $(INC) -fPIC
DEPS= ../iotHandler.h ../../src/pdp1/pdp1.h ../../src/pdp1/dynamicIots.h \
      ../../src/pdp1/highSpeedChannels.h ../../src/pdp1/configuration.h \
      ../../src/pdp1/ad1intf.h
# The emulator's Makefile writes sdl3.h and its clean removes it; IOT_71.c includes it only
# if it is there, so it is a prerequisite only then.
SDL3H= $(wildcard ../../src/pdp1/sdl3.h)

all: IOT_71.so IOT_72.so

IOT_71.so: IOT_71.c room.h edge.h ../Lib/iotLogger.h $(SDL3H) $(DEPS)
	$(CC) $(CFLAGS) -shared IOT_71.c -o $@ -lm

IOT_72.so: IOT_72.c $(DEPS)
	$(CC) $(CFLAGS) -shared IOT_72.c -o $@

install: IOT_71.so IOT_72.so
	cp IOT_71.so IOT_72.so ..

clean:
	@rm -f *.so

.PHONY: all install clean
