# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile. -fPIC belongs in CFLAGS for plugins.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
INC= -I../src/common -I../src/pdp1 -ILib
CFLAGS += $(INC) -fPIC
files := $(wildcard *.c)

%.so:%.o
	$(CC) $(CFLAGS) -shared $< -o $@
%.o:%.c iotHandler.h ../src/pdp1/dynamicIots.h ../src/pdp1/pdp1.h ../src/pdp1/ad1intf.h
	$(CC) $(CFLAGS) -c $< -o $@

all: dist $(files:.c=.so)

dist:
	./install.sh
clean:
	@rm *.o *.so 2>/dev/null || true
	./cleanall.sh
