# The tree-wide build convention: environment CC/CFLAGS (rpmbuild's %optflags)
# win; the ?= defaults are for a bare source build; requirements are appended.
# See src/pdp1/Makefile.
CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra
CFLAGS += -std=c99 -I../common
TARGET3=pdp1_usb_monitor
SOURCE3=pdp1_usb_monitor.c
LIBS=-ludev

all: $(TARGET) $(TARGET2) $(TARGET3)

$(TARGET3): $(SOURCE3)
	$(CC) $(CFLAGS) -o $(TARGET3) $(SOURCE3)

clean:
	rm -f $(TARGET) $(TARGET2) $(TARGET3)

#install: $(TARGET3)
#	sudo cp $(TARGET3) /usr/local/bin/
#	sudo chmod +x /usr/local/bin/$(TARGET3)

#.PHONY: all clean install
