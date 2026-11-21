# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile. The blanket -w this Makefile used to put on the
# compiler is now only on glad/, whose code is generated.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra

SRC=main.c p7.c ptape.c typewriter.c ../common/common.c checkConfig.c \
	../common/logger.c
INC=-I../common
CFLAGS += $(INC)
LIBS=-lSDL2_ttf

all: pdp1_periph pdp1_periphES

pdp1_periph: $(SRC) glad/glad.o
	$(CC) $(CFLAGS) -o $@ $^ -lm -ldl -lpthread `sdl2-config --cflags --libs` $(LIBS)
pdp1_periphES: $(SRC) glad/glad.o
	$(CC) $(CFLAGS) -DGLES -o $@ $^ -lm -ldl -lpthread `sdl2-config --cflags --libs` $(LIBS)

# glad's loader is generated code; its warnings are not ours to fix. Without
# this rule the implicit one would compile it with the same warnings as the
# hand-written sources.
glad/glad.o: glad/glad.c
	$(CC) $(CFLAGS) -w -c -o $@ $<
