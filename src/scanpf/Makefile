INC=-I../common
LIBS=-lpthread -lm

all: scanpf

scanpf: main.c ../common/common.c
	cc -O3 -o $@ $^ $(INC) $(LIBS)

clean:
	@rm -f scanpf 2>/dev/null || true

.PHONY: all clean
