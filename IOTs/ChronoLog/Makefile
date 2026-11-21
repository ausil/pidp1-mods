# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC= -I../../src/common -I../../src/pdp1 -I.. -I../Lib
CFLAGS += $(INC) -fPIC

%.o:%.c ../iotHandler.h ../../src/pdp1/dynamicIots.h ../../src/pdp1/pdp1.h ../../src/pdp1/ad1intf.h ../Lib/iotLogger.h
	$(CC) $(CFLAGS) -c $< -o $@
%.so:%.o ../Lib/iotLogger.o
	$(CC) $(CFLAGS) -shared $< ../Lib/iotLogger.o -o $@

install: IOT_70.so
	cp *.so ..

clean:
	@rm *.o *.so 2>/dev/null || true

# Lib's objects are built by its own Makefile, which knows their headers.
../Lib/%.o: FORCE
	$(MAKE) -C ../Lib $*.o

FORCE:
