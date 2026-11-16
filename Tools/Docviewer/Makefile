CC=gcc -O2

all: docviewer

docviewer: docviewer.c
	$(CC) -o docviewer docviewer.c

install: docviewer
	cp docviewer ../../bin/docviewer
	strip ../../bin/docviewer

clean:
	@rm docviewer 2>/dev/null || true
