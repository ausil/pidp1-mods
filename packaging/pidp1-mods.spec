# pidp1-mods.spec -- RPM for the PiDP-1 simulator tree.
#
# Build it from a checkout with `make rpm` (which runs packaging/build-rpm.sh:
# a git archive of HEAD staged in dist/, products written flat to dist-rpm/).
# `make rpmlint` builds and lints; exceptions live in packaging/rpmlint.toml
# with a reason each. COPR uses .copr/Makefile, the same script --srpm-only.
#
# The layout is the one src/common/pidp1_paths.h and bin/pidp1-env.sh
# describe; they are the single source of truth and must agree with %%files:
#
#   /usr/share/pidp1-mods    read-only program data, a mirror of the checkout:
#                            the tape library, Microtapes, Drums, Am1Includes,
#                            Docs, FunStuff, the web assets, and bin/ with the
#                            helper scripts.
#   /var/lib/pidp1-mods      what the running machine writes: the Type 23 drum
#                            image, coremem, punch.out, and tapes/ and
#                            bootcfg/, seeded on first install from the
#                            read-only masters above (tmpfiles recreates the
#                            directories; %%post does the copying).
#   /etc/pidp1-mods          the site's configuration, %%config(noreplace):
#                            pidp1.config, t30dpy.config, microtapes.txt,
#                            usb_paper_tape_ports.cfg.
#   /usr/lib/pidp1-mods/IOTs the dynamic IOT plugins the emulator dlopen()s by
#                            absolute path -- plain /usr/lib on every
#                            architecture; they are never on the linker's
#                            search path, so multilib buys nothing.
#   /usr/libexec/pidp1-mods  the programs the scripts start rather than users
#                            type (the emulator, panel drivers, peripherals,
#                            the web server).
#   /usr/bin                 the user commands, matching the checkout install's
#                            /usr/local/bin set; man pages for the front doors.
#
# The group pidp1-mods, created by the sysusers fragment (Source1), owns the
# writable parts: the state directory (Source2's tmpfiles fragment keeps them
# alive), /etc/pidp1-mods (pdp1central saves pidp1.config), and the
# Microtapes/ and Drums/ data subdirectories the IOTs and drum tools write
# images into. Operators run: usermod -aG pidp1-mods <name>.
#
# Deliberate deviations, expanded in packaging/README.md: no systemd service
# (the simulator is interactive; pdp1control is the front door), no subpackage
# split yet (a -panel split waits for hardware and headless boxes to diverge),
# no setuid on the hardware panel driver (a cabinet runs
# src/panel_pidp1/setpriv.sh, or waits for libgpiod plus a udev rule), and one
# vendored blob: web_pdp1/vendor, gorilla/websocket, so %%build needs no
# network. rpmlint's exceptions, each with its reason, are in rpmlint.toml.

%global srcdate 20261115

%global debug_package %{nil}

Name:           pidp1-mods
Version:        1.0
Release:        1.%{srcdate}%{?dist}
Summary:        PDP-1 simulator, PiDP-1 panel drivers, assembler and tools
License:        MIT AND BSD-2-Clause
URL:            https://github.com/ausil/pidp1-mods
# a git archive of this repository, staged by packaging/build-rpm.sh: there is
# nothing to download (see rpmlint.toml's invalid-url filter)
Source0:        %{name}-%{version}-%{srcdate}.tar.gz
# staged from packaging/systemd/ by build-rpm.sh; the create_package macros
# read them at parse time, so they must be in _sourcedir before rpmbuild runs
Source1:        pidp1-mods.sysusers.conf
Source2:        pidp1-mods.tmpfiles.conf

BuildRequires:  gcc, make, flex, bison, zlib-devel
BuildRequires:  desktop-file-utils, systemd-rpm-macros
BuildRequires:  pkgconfig(sdl2) pkgconfig(SDL2_image) pkgconfig(SDL2_ttf)
BuildRequires:  golang, python3

Requires:       systemd nmap-ncat screen zenity python3 python3-tk lxterminal telnet
Recommends:     golang
# the noisy Teletype model 33 that `pdp1 con` starts (its sty, PIDP10_STY)
Suggests:       pidp10

%description
A PDP-1 emulator with the PiDP-1 physical and virtual front panels, the Type 23
drum and Type 550 microtape IOTs, the am1 macro assembler, the ad1 debugger, the
t30dpy Type 30 display, and the rest of the pdp1 / pdp1control / pdp1central
tool set. The FHS layout matches src/common/pidp1_paths.h and bin/pidp1-env.sh,
so a packaged install and a source checkout behave the same.

%prep
%autosetup -n %{name}-%{version}-%{srcdate}

%build
# One build list for everything: the same script install.sh runs. It skips the
# SDL2_image/SDL2_ttf/go pieces with a warning when their development files are
# missing; the BuildRequires above mean that does not happen here.
export GOCACHE=%{_builddir}/gocache
export GOPATH=%{_builddir}/go
bash install/build-all.sh

%install
rm -rf %{buildroot}
datadir=%{buildroot}%{_datadir}/pidp1-mods
statedir=%{buildroot}%{_sharedstatedir}/pidp1-mods
iotdir=%{buildroot}%{_prefix}/lib/pidp1-mods/IOTs
libexec=%{buildroot}%{_libexecdir}/pidp1-mods

# ---------------------------------------------------------------------------
# The read-only tree, shaped the way an unpacked checkout is: the programs
# find their pieces under DATADIR the same way they find them in the tree.
# ---------------------------------------------------------------------------
mkdir -p $datadir
cp -a Am1Includes MacroIncludes Docs Drums Microtapes tapes bootcfg Diagnostics \
      FunStuff web_pdp1 $datadir/
rm -f $datadir/web_pdp1/pdpsrv                 # built binary belongs in libexec
cp -a pdp23drum.example pidp1.config.example $datadir/
mkdir -p $datadir/src/pdp1_periph
install -m 644 src/pdp1_periph/DejaVuSansMono.ttf $datadir/src/pdp1_periph/

# bin/ keeps only the scripts: pdp1central runs bin/pdp1control.sh, bin/askfile
# and bin/save_ptp.sh from here, and the scripts source bin/pidp1-env.sh.
mkdir -p $datadir/bin
for f in bin/*; do
    if [ -f "$f" ] && ! head -c 4 "$f" | grep -q ELF; then
        cp -a "$f" $datadir/bin/
    fi
done
# per-directory .gitignore files (the vendored tree, the FunStuff experiments)
# are checkout noise, not installed data
find $datadir -name .gitignore -delete
# go mod vendor leaves an empty go.sum in the vendored package; nothing reads
# it (build-time consistency is vendor/modules.txt's job) and a zero-length
# file in a package is rpmlint E:
find $datadir/web_pdp1/vendor -type f -name go.sum -empty -delete
# pdp1central and the wrappers run these by path through a shell, so they
# need the exec bit (and a shebang on a non-executable file is rpmlint E:);
# being runnable by hand is harmless for the ones only launched as
# "python3 <file>".
chmod 755 $datadir/bin/*
find $datadir -name '*.py' -exec chmod 755 {} +
# the packaging notes travel with the binaries; named so they cannot land on
# top of the project README in the shared doc dir (see %%files)
cp packaging/README.md ./PACKAGING.md

# ---------------------------------------------------------------------------
# Binaries. The user commands go in /usr/bin, matching what the checkout
# install puts in /usr/local/bin; the ones the scripts start go in libexec.
# ---------------------------------------------------------------------------
mkdir -p %{buildroot}%{_bindir} $libexec
for t in ad1 am1 asr33tape disassemble docviewer drumlist drumupdater fastload \
         fstool mactoam1 mkmicrotape mtp ovlload pdp1audio scanpf t30dpy tapevis; do
    install -m 755 bin/$t %{buildroot}%{_bindir}/
done
install -m 755 bin/macro1_1 %{buildroot}%{_bindir}/
ln -s macro1_1 %{buildroot}%{_bindir}/macro1
install -m 755 src/pdp1central/pdp1central %{buildroot}%{_bindir}/
# scripts are installed once, in $datadir/bin, and named from /usr/bin by
# symlink: a byte-identical copy would be (and was) hardlinked onto both
# paths by brp-hardlink-dupes, which rpmlint rightly calls a cross-partition
# hardlink. The scripts locate pidp1-env.sh and their Python siblings beside
# their resolved path, so the symlink resolves to $datadir/bin and both
# lookups land in the same tree.
ln -s ../share/pidp1-mods/bin/pdp1.sh           %{buildroot}%{_bindir}/pdp1
ln -s ../share/pidp1-mods/bin/pdp1control.sh    %{buildroot}%{_bindir}/pdp1control
ln -s ../share/pidp1-mods/bin/tkaskopenfile     %{buildroot}%{_bindir}/tkaskopenfile
ln -s ../share/pidp1-mods/bin/tkaskopenfilewrite %{buildroot}%{_bindir}/tkaskopenfilewrite
ln -s ../share/pidp1-mods/bin/encode_fiodec     %{buildroot}%{_bindir}/encode_fiodec
ln -s ../share/pidp1-mods/bin/decode_fiodec     %{buildroot}%{_bindir}/decode_fiodec
ln -s ../share/pidp1-mods/bin/tape_visualizer   %{buildroot}%{_bindir}/tape_visualizer

install -m 755 src/pdp1/pdp1                     $libexec/pdp1
install -m 755 src/panel_pidp1/newpanel          $libexec/panel_pidp1
install -m 755 src/vpanel_pdp1/panel_pdp1        $libexec/vpanel_pdp1
install -m 755 src/pdp1_periph/pdp1_periph       $libexec/
install -m 755 src/pdp1_periph/pdp1_periphES     $libexec/
install -m 755 src/usb_paper_tape/pdp1_usb_monitor $libexec/
install -m 755 src/ptytools/mkptyfio src/ptytools/mkptyfl $libexec/
install -m 755 web_pdp1/pdpsrv                   $libexec/

mkdir -p $iotdir
install -m 755 IOTs/*.so $iotdir/

# debug_package is off, so nothing else would take the symbol tables: strip
# every installed ELF (the head test skips the scripts and symlinks; the
# tools' install rules already stripped their own copies in bin/)
for f in $libexec/* $iotdir/* %{buildroot}%{_bindir}/*; do
    if [ -f "$f" ] && [ "$(head -c 4 "$f" | tr -d '\000-\040\177')" = ELF ]; then
        strip -s "$f"
    fi
done

# ---------------------------------------------------------------------------
# Configuration and state. The writable bits are group pidp1-mods (created by
# the sysusers fragment in %%pre) so a panel driver started by any member can
# write them. The tmpfiles fragment (Source2) recreates the state directories;
# %%post seeds what belongs in them once.
# ---------------------------------------------------------------------------
mkdir -p %{buildroot}%{_sysconfdir}/pidp1-mods
cp -a pidp1.config.example    %{buildroot}%{_sysconfdir}/pidp1-mods/pidp1.config
cp -a t30dpy.config.example   %{buildroot}%{_sysconfdir}/pidp1-mods/t30dpy.config
cp -a microtapes.txt.example  %{buildroot}%{_sysconfdir}/pidp1-mods/microtapes.txt
cp -a bin/usb_paper_tape_ports.cfg %{buildroot}%{_sysconfdir}/pidp1-mods/

mkdir -p -m 775 $statedir $statedir/tapes $statedir/bootcfg

# ---------------------------------------------------------------------------
# Man pages for the front doors, desktop entries, and their theme icons (the
# same hicolor names install.sh creates in the user's theme for a checkout).
# ---------------------------------------------------------------------------
install -Dm 0644 man/pdp1.1 %{buildroot}%{_mandir}/man1/pdp1.1
install -Dm 0644 man/pdp1control.1 %{buildroot}%{_mandir}/man1/pdp1control.1

# the vendored gorilla/websocket's notice, named after what it covers so it
# does not collide with the project LICENSE in the licenses directory
install -Dm 0644 web_pdp1/vendor/github.com/gorilla/websocket/LICENSE \
    %{buildroot}%{_prefix}/share/licenses/%{name}/LICENSE.gorilla-websocket

mkdir -p %{buildroot}%{_datadir}/applications
install -m 644 install/audioOff.desktop install/audioOn.desktop \
               install/pdp1central.desktop install/pdp1control.desktop \
               install/pdp1startup.desktop install/ptp.desktop install/ptr.desktop \
               install/t30dpy.desktop install/tty.desktop \
               %{buildroot}%{_datadir}/applications/
icondir=%{buildroot}%{_datadir}/icons/hicolor/scalable/apps
mkdir -p $icondir
install -m 644 install/pdp1icon2.svg     $icondir/pdp1.svg
install -m 644 install/pdp1central.svg    $icondir/
install -m 644 install/pdp1control.svg    $icondir/
install -m 644 install/t30dpy.svg         $icondir/
install -m 644 install/ptr-icon.svg       $icondir/pidp1-ptp.svg
install -m 644 install/ptr-icon.svg       $icondir/pidp1-ptr.svg
install -m 644 install/soroban-icon2.svg  $icondir/soroban.svg

# The two OS-integration fragments, so a checkout and the build see one copy
install -Dm 0644 %{SOURCE1} %{buildroot}%{_sysusersdir}/pidp1-mods.conf
install -Dm 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/pidp1-mods.conf

%check
# the desktop entries must actually parse, and the mactoam1 fixture legs must
# pass with the am1 and converter built above. The t1 corpus leg is skipped:
# its src/blincolnlights corpus is not part of this tree (run_tests.sh wants
# it checked out), and the control leg rebuilds git history - neither exists
# in an RPM build. Revisit t1 when the corpus ships with the package.
for d in %{buildroot}%{_datadir}/applications/*.desktop; do
    desktop-file-validate "$d" || exit 1
done
bash Tools/MtoA/Tests/run_tests.sh -w %{_builddir}/mtoatest t2 t3

%pre
%sysusers_create_package %{name} %{SOURCE1}

%post
%tmpfiles_create_package %{name} %{SOURCE2}
st=%{_sharedstatedir}/pidp1-mods
da=%{_datadir}/pidp1-mods
# seed once; never overwrite what the site already put in the state directory
if [ ! -f $st/pdp23drum ]; then
    cp -a $da/pdp23drum.example $st/pdp23drum
    chgrp pidp1-mods $st/pdp23drum
    chmod 0664 $st/pdp23drum
fi
cp -aN $da/tapes/.   $st/tapes/   2>/dev/null || :
cp -aN $da/bootcfg/. $st/bootcfg/ 2>/dev/null || :
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor 2>/dev/null || :

%postun
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor 2>/dev/null || :

%files
%license LICENSE
%license %{_prefix}/share/licenses/%{name}/LICENSE.gorilla-websocket
%doc README.md RELEASENOTES.txt PACKAGING.md
%{_mandir}/man1/pdp1.1*
%{_mandir}/man1/pdp1control.1*
%{_bindir}/ad1
%{_bindir}/am1
%{_bindir}/asr33tape
%{_bindir}/decode_fiodec
%{_bindir}/disassemble
%{_bindir}/docviewer
%{_bindir}/drumlist
%{_bindir}/drumupdater
%{_bindir}/encode_fiodec
%{_bindir}/fastload
%{_bindir}/fstool
%{_bindir}/mactoam1
%{_bindir}/macro1
%{_bindir}/macro1_1
%{_bindir}/mkmicrotape
%{_bindir}/mtp
%{_bindir}/ovlload
%{_bindir}/pdp1
%{_bindir}/pdp1audio
%{_bindir}/pdp1central
%{_bindir}/pdp1control
%{_bindir}/scanpf
%{_bindir}/t30dpy
%{_bindir}/tapevis
%{_bindir}/tape_visualizer
%{_bindir}/tkaskopenfile
%{_bindir}/tkaskopenfilewrite
%{_libexecdir}/pidp1-mods/
%{_prefix}/lib/pidp1-mods/
# the read-only tree, spelled out per child so the two group-writable
# subdirectories below can carry their %%attr (a recursive line could not)
%dir %{_datadir}/pidp1-mods
%{_datadir}/pidp1-mods/Am1Includes
%{_datadir}/pidp1-mods/MacroIncludes
%{_datadir}/pidp1-mods/Docs
%{_datadir}/pidp1-mods/Diagnostics
%{_datadir}/pidp1-mods/FunStuff
%{_datadir}/pidp1-mods/bin
%{_datadir}/pidp1-mods/bootcfg
%{_datadir}/pidp1-mods/src
%{_datadir}/pidp1-mods/tapes
%{_datadir}/pidp1-mods/web_pdp1
%{_datadir}/pidp1-mods/pdp23drum.example
%{_datadir}/pidp1-mods/pidp1.config.example
%dir %attr(2775, root, pidp1-mods) %{_datadir}/pidp1-mods/Microtapes
%attr(0664, root, pidp1-mods) %{_datadir}/pidp1-mods/Microtapes/*
%dir %attr(2775, root, pidp1-mods) %{_datadir}/pidp1-mods/Drums
%attr(0664, root, pidp1-mods) %{_datadir}/pidp1-mods/Drums/*
%{_sysusersdir}/pidp1-mods.conf
%{_tmpfilesdir}/pidp1-mods.conf
%{_datadir}/applications/audioOff.desktop
%{_datadir}/applications/audioOn.desktop
%{_datadir}/applications/pdp1central.desktop
%{_datadir}/applications/pdp1control.desktop
%{_datadir}/applications/pdp1startup.desktop
%{_datadir}/applications/ptp.desktop
%{_datadir}/applications/ptr.desktop
%{_datadir}/applications/t30dpy.desktop
%{_datadir}/applications/tty.desktop
%{_datadir}/icons/hicolor/scalable/apps/pdp1.svg
%{_datadir}/icons/hicolor/scalable/apps/pdp1central.svg
%{_datadir}/icons/hicolor/scalable/apps/pdp1control.svg
%{_datadir}/icons/hicolor/scalable/apps/pidp1-ptp.svg
%{_datadir}/icons/hicolor/scalable/apps/pidp1-ptr.svg
%{_datadir}/icons/hicolor/scalable/apps/t30dpy.svg
%{_datadir}/icons/hicolor/scalable/apps/soroban.svg
%config(noreplace) %{_sysconfdir}/pidp1-mods/usb_paper_tape_ports.cfg
# writable-by-group: the members of pidp1-mods run the machine
%dir %attr(2775, root, pidp1-mods) %{_sharedstatedir}/pidp1-mods
%dir %attr(2775, root, pidp1-mods) %{_sharedstatedir}/pidp1-mods/tapes
%dir %attr(2775, root, pidp1-mods) %{_sharedstatedir}/pidp1-mods/bootcfg
%dir %attr(2775, root, pidp1-mods) %{_sysconfdir}/pidp1-mods
%attr(0664, root, pidp1-mods) %config(noreplace) %{_sysconfdir}/pidp1-mods/pidp1.config
%attr(0664, root, pidp1-mods) %config(noreplace) %{_sysconfdir}/pidp1-mods/t30dpy.config
%attr(0664, root, pidp1-mods) %config(noreplace) %{_sysconfdir}/pidp1-mods/microtapes.txt

%changelog
* Sun Nov 15 2026 Dennis Gilmore <dennis@ausil.us> - 1.0-1.20261115
- Initial packaged layout: FHS homes per src/common/pidp1_paths.h and
  bin/pidp1-env.sh, one build list in install/build-all.sh, sysusers and
  tmpfiles for the pidp1-mods group and state, desktop entries, hicolor
  icons, man pages for pdp1 and pdp1control.
