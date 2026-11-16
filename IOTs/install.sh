#!/bin/bash
#
# Build every dynamic IOT and leave the resulting .so files in this directory, which is
# where the emulator dlopen()s them from. Run through "make -C IOTs all".
#
# Everything is relative to this directory, it used to "cd /opt/pidp1-mods/IOTs" between
# the subdirectories, which quietly built only the first one anywhere but in /opt.

cd "$(dirname "$0")" || exit 1

cd Lib && make || exit 1
cd .. || exit 1

for F in $(find * -type d -not -name Tests); do
    echo Building "$F"
    ( cd "$F" && pwd && make install ) || exit 1
done

strip --strip-unneeded *.so
