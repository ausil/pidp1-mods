# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build. These two programs are
# single files built by make's implicit rules, which honour CC and CFLAGS.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra

all: mkptyfio mkptyfl
