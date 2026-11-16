CFLAGS= $(INC) -O3 -Wno-unused-result

# The libgpiod backend (gpiolib_gpiod.c) is compiled in when the development
# files are present; absent them the build falls back to the register-mapping
# backend alone, exactly as before. Detection is duplicated in
# src/panel_pidp1/Makefile (which must add -lgpiod at the link); both ask
# pkg-config the same question, so the two agree by construction.
HAVE_PKGCONFIG := $(shell command -v pkg-config >/dev/null 2>&1 && echo 1)
ifeq ($(HAVE_PKGCONFIG),1)
HAVE_GPIOD := $(shell pkg-config --exists libgpiod 2>/dev/null && echo 1)
ifeq ($(HAVE_GPIOD),1)
CFLAGS += -DHAVE_GPIOD $(shell pkg-config --cflags libgpiod)
endif
endif

SRC := $(wildcard *.c)
OBJ := $(SRC:.c=.o)

all: $(OBJ)
	cc -c $(CFLAGS) $(SRC)

clean:
	@rm *.o >/dev/null 2>&1 || true
