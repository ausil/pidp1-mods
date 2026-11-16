INC=-I../common
LIBS=-lpthread -lm

all: pidp1_test

pidp1_test: main.c ../common/common.c
	cc -O3 -o $@ $^ $(INC) $(LIBS)

clean:
	@rm -f pidp1_test 2>/dev/null || true

.PHONY: all clean
