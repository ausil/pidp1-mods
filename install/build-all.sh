#!/bin/bash
#
# One-shot, non-interactive build of every program in this repository.
#
#   install/build-all.sh              build everything, populate bin/
#   install/build-all.sh --tar        also write bin/binaries-for-$(uname -m).tar.gz
#
# This is the "make required binaries" step of install.sh, split out so it can be run
# on its own (and by whoever prepares the precompiled binary drop). install.sh calls it,
# so there is only one list of things to build.
#
# It builds where the tree actually lives; nothing here requires /opt/pidp1-mods, though
# the emulator only finds the dynamic IOT plugins when it is installed there.
#
# Optional programs need SDL2_image (the virtual panel) and SDL2_ttf (the peripheral
# simulator); when those development packages are missing the program is skipped with a
# warning instead of failing the whole build.

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1

makeTars=0
for arg in "$@"; do
    case "$arg" in
        --tar) makeTars=1 ;;
        -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
        *) echo "unknown argument: $arg"; exit 1 ;;
    esac
done

fails=()
skips=()

# Run make in a directory (no target means the directory's default one). A failure is
# remembered, it does not abort the build: one broken corner should not stop the other
# dozen programs from being built.
build() {
    local dir="$1" target="${2:-}"
    if [ -n "$target" ]; then
        echo "=== make -C $dir $target"
    else
        echo "=== make -C $dir"
    fi
    if ! make -C "$dir" $target; then
        echo "!!! $dir: '${target:-default}' failed"
        fails+=("$dir $target")
        return 1
    fi
    return 0
}

# Does an #include of this header compile? With sdl2-config's flags, which are present
# whenever SDL2's development files are. Used for the two optional SDL pieces.
have_sdl_header() {
    local hdr="$1"
    printf '#include <%s>\nint main(void){return 0;}\n' "$hdr" > /tmp/pidp1hdr.$$.c
    if cc /tmp/pidp1hdr.$$.c $(sdl2-config --cflags --libs) -o /tmp/pidp1hdr.$$ >/dev/null 2>&1; then
        rm -f /tmp/pidp1hdr.$$.c /tmp/pidp1hdr.$$
        return 0
    fi
    rm -f /tmp/pidp1hdr.$$.c /tmp/pidp1hdr.$$
    return 1
}

echo "Building PiDP-1 from $root"
echo

# ---------------------------------------------------------------------------
# The emulator, its panel drivers and the programs that talk to the hardware
# ---------------------------------------------------------------------------
build src/pdp1                            # the emulator
build src/panel_pidp1                     # physical front panel driver (newpanel)
build src/scanpf                          # front panel switch reader
build src/tapevis                         # rim tape visualizer
build src/pidp1_test                      # hardware test program
build src/pdp1central                     # the desktop control app
build src/ptytools                        # mkptyfio / mkptyfl, the pty front ends
build src/usb_paper_tape                  # pdp1_usb_monitor

# The virtual panel needs SDL2_image.
if have_sdl_header SDL2/SDL_image.h; then
    build src/vpanel_pdp1
else
    echo "--- skipping the virtual panel, SDL2_image development files not found"
    skips+=("src/vpanel_pdp1 (needs SDL2_image)")
fi

# The peripheral simulator needs SDL2_ttf.
if have_sdl_header SDL_ttf.h; then
    build src/pdp1_periph
else
    echo "--- skipping the peripheral simulator, SDL2_ttf development files not found"
    skips+=("src/pdp1_periph (needs SDL2_ttf)")
fi

# ---------------------------------------------------------------------------
# The macro1_1 cross assembler, a single source file with no makefile
# ---------------------------------------------------------------------------
echo "=== macro1_1"
if ! cc -O3 src/macro/macro1_1.c -o src/macro/macro1_1; then
    echo "!!! src/macro/macro1_1.c failed"
    fails+=("src/macro/macro1_1.c")
fi

# ---------------------------------------------------------------------------
# The dynamic IOT plugins. Clean first: a stale .so from an earlier build would
# otherwise be shipped again unnoticed.
# ---------------------------------------------------------------------------
build IOTs clean
build IOTs all

# ---------------------------------------------------------------------------
# Tools. Each has its own install rule that copies (and strips) into bin/; their
# cleans are run afterwards so only bin/ holds binaries, not the source directories.
# ---------------------------------------------------------------------------
build Tools/UtilLibs
build Tools/AM1 install
build Tools/AM1 clean
build Tools/AD1 install
build Tools/AD1 clean
build Tools/Drumupdater install
build Tools/Drumupdater clean
build Tools/Utils install          # mtp, fstool, asr33tape
build Tools/Utils clean
build Tools/Ovlload install
build Tools/Ovlload clean
build Tools/T30dpy install         # picks SDL3 or SDL2 by itself
build Tools/T30dpy clean
build Tools/MtoA install
build Tools/MtoA clean
build Tools/Disassembler install
build Tools/Disassembler clean
build Tools/Docviewer install
build Tools/Docviewer clean
build IOTs/Microtape install       # mkmicrotape
build IOTs/Microtape clean
build Tools install                # pdp1audio
build Tools clean

# ---------------------------------------------------------------------------
# The web front end. Only when Go is installed; the browser UI is optional.
# ---------------------------------------------------------------------------
if command -v go >/dev/null 2>&1; then
    echo "=== go build web_pdp1"
    ( cd web_pdp1 && go build -o pdpsrv . ) || {
        echo "!!! web_pdp1 build failed"
        fails+=("web_pdp1")
    }
else
    echo "--- skipping the web server, go is not installed"
    skips+=("web_pdp1 (needs golang)")
fi

# ---------------------------------------------------------------------------
# bin/ holds one name per program. The source directories keep their own copies so
# a rebuild needs no extra step, but everything is reachable from bin/.
# ---------------------------------------------------------------------------
link() {   # link <target> <name in bin>
    if [ -f "$1" ]; then
        ln -sf "$root/$1" "$root/bin/$2"
    else
        echo "--- $1 was not built, bin/$2 not created"
    fi
}

link src/pdp1/pdp1                      pdp1
link src/panel_pidp1/newpanel           panel_pidp1
link src/vpanel_pdp1/panel_pdp1         vpanel_pdp1
link src/scanpf/scanpf                  scanpf
link src/tapevis/tapevis                tapevis
link src/pidp1_test/pidp1_test          pidp1_test
link src/pdp1central/pdp1central        pdp1central
link src/pdp1_periph/pdp1_periph        pdp1_periph
link src/pdp1_periph/pdp1_periphES      pdp1_periphES
link src/usb_paper_tape/pdp1_usb_monitor pdp1_usb_monitor
link src/macro/macro1_1                 macro1_1
link src/ptytools/mkptyfio              mkptyfio
link src/ptytools/mkptyfl               mkptyfl
link web_pdp1/pdpsrv                    pdpsrv

# The old names of the disassembler, removed when it was renamed.
rm -f "$root/bin/disassemble_tape" "$root/bin/disassemble_mem"

echo
if [ ${#skips[@]} -gt 0 ]; then
    echo "Skipped:"
    for s in "${skips[@]}"; do echo "  - $s"; done
    echo
fi
if [ ${#fails[@]} -gt 0 ]; then
    echo "FAILED builds:"
    for f in "${fails[@]}"; do echo "  - $f"; done
    echo
    exit 1
fi
echo "All builds succeeded, bin/ is populated."

# ---------------------------------------------------------------------------
# The precompiled binary drop, same shape as the other PiDP repositories: untar it
# over bin/ on a machine of the same architecture and nothing has to be compiled.
# The dynamic IOT plugins go along, they are dlopen()ed by the emulator.
# ---------------------------------------------------------------------------
if [ "$makeTars" = "1" ]; then
    arch="$(uname -m)"
    tarball="$root/bin/binaries-for-$arch.tar.gz"
    files=()
    for f in "$root"/bin/*; do
        # follows the symlinks created above; the shell scripts in bin/ are not ELF,
        # they are already in the repository and need no packaging
        [ -f "$f" ] || continue
        if [ "$(head -c 4 "$f" | tr -d '\000-\040\177')" = "ELF" ]; then
            files+=("${f#$root/}")
        fi
    done
    for f in "$root"/IOTs/*.so; do
        [ -f "$f" ] && files+=("${f#$root/}")
    done
    echo
    echo "Writing $tarball (${#files[@]} files)"
    # -h dereferences, -c keeps the modification time so an unchanged rebuild
    # produces the same list of members.
    tar -czf "$tarball" -C "$root" -h "${files[@]}" || {
        echo "!!! writing $tarball failed"
        exit 1
    }
    ls -l "$tarball"
fi

exit 0
