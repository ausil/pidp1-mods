#!/bin/bash
# Run `make clean` in every IOT subdirectory except the Tests ones. The
# shebang is load-bearing: without one the kernel hands the script back
# ENOEXEC, and while a native build survives on the shell's fallback, mock's
# forcearch riscv64 root (qemu-user) exits 127 on the direct exec.
for F in `find * -type d -not -name Tests`; do
    cd $F
    pwd
    make clean
    cd ..
done
