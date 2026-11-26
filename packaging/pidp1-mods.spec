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
#                            Microtapes, Drums, Am1Includes, MacroIncludes,
#                            Docs, FunStuff, the web assets, and bin/ with the
#                            helper scripts.
#   /var/lib/pidp1-mods      what the running machine reads and writes: the
#                            Type 23 drum image, coremem, punch.out, and the
#                            shipped tape library and boot configurations in
#                            tapes/ and bootcfg/ -- package content living
#                            where the machine looks for it (pidp1_paths.h
#                            PIDP1_TAPEDIR, pidp1-env.sh PIDP1_TAPES), owned
#                            by the package as %%config(noreplace): site
#                            edits survive upgrades (the shipped update
#                            lands as .rpmnew), files the site added itself
#                            are left alone, and tmpfiles recreates the
#                            directories.
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
# The group pidp1, created by the sysusers fragment (Source1), is the
# cabinet's operator group and owns the writable parts: the state directory
# (Source2's tmpfiles fragment keeps them alive), /etc/pidp1-mods (pdp1central
# saves pidp1.config), and the Microtapes/ and Drums/ data subdirectories the
# IOTs and drum tools write images into. The same group gets the panel's GPIO
# nodes from the shipped udev rule and the machine's console from the shipped
# sudoers fragment (/etc/sudoers.d/pidp1-mods: sudo -u pidp1). The service
# account is pidp1 too - user and group share the name, and nothing named
# pidp1-mods is a user or group anywhere. Operators run:
# usermod -aG pidp1 <name>.
#
# Deliberate deviations, expanded in packaging/README.md: the boot-time
# systemd units (pdp1, pdp1-panel, pdp1-bootcfg) ship preset-disabled --
# installing the package never starts the simulator on its own; the desktop
# front door remains pdp1control and the cabinet operator enables the units
# once, one subpackage split already (%%{name}-clients carries the programs
# that talk to a remote pdp1 -- t30dpy, tapevis, ad1 -- for machines that
# watch or debug the machine rather than being it; a -panel split waits for
# hardware and headless boxes to diverge),
# no setuid on the hardware panel driver (newpanel's libgpiod backend drives
# the panel through /dev/gpiochipN, and the shipped zz-pidp1-mods.rules hands
# the panel's controller to the pidp1 group -- zz-* so it loads after the
# 99-* rules the sibling cabinet packages ship for the same chip, since a
# node has one group and the last match wins; src/panel_pidp1/setpriv.sh is
# left for the /dev/mem fallback on kernels that have neither gpiomem nor
# gpiochip access), no firewall port opened at install (every server binds to
# all interfaces on purpose -- a web front end or a t30dpy on another machine
# is the design -- so remote access is the operator's call, taken with the two
# opt-in firewalld services installed under /usr/lib/firewalld/services), and
# one vendored blob: web_pdp1/vendor, gorilla/websocket, so %%build needs no
# network. rpmlint's exceptions, each with its reason, are in rpmlint.toml.

%global srcdate 20261125

Name:           pidp1-mods
Version:        1.0
Release:        5.%{srcdate}%{?dist}
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
BuildRequires:  pkgconfig(libgpiod)
BuildRequires:  golang, python3

Requires:       systemd nmap-ncat screen zenity python3 python3-tkinter lxterminal telnet
# udevadm in the scriptlets that reload the panel rule
Requires(post): systemd-udev
Recommends:     golang
# the console attach in pdp1.sh: sudo -u pidp1 pidp1-attach, allowed
# for the pidp1 group by the shipped sudoers fragment
Recommends:     sudo
# pdp1control start/apps launches t30dpy and tapevis beside the machine, so
# a cabinet install keeps the clients by default; a remote operator installs
# just the subpackage
Recommends:     %{name}-clients = %{version}-%{release}
# the noisy Teletype model 33 that `pdp1 con` starts (its sty, PIDP10_STY)
Suggests:       pidp10

%description
A PDP-1 emulator with the PiDP-1 physical and virtual front panels, the Type 23
drum and Type 550 microtape IOTs, the am1 macro assembler, the ad1 debugger,
and the rest of the pdp1 / pdp1control / pdp1central tool set. The FHS layout
matches src/common/pidp1_paths.h and bin/pidp1-env.sh, so a packaged install
and a source checkout behave the same. The programs that watch or debug a
remote machine over the network -- t30dpy, tapevis, ad1 -- are the separate
pidp1-mods-clients, which needs none of this.

%package clients
Summary:        Clients for watching and debugging a remote PDP-1

%description clients
The programs that talk to a pdp1 over the network instead of being the
machine: the t30dpy Type 30 vector display (display port 3400 plus the
screen number), the tapevis paper tape reader and punch (1042 and 1043),
and the ad1 debugger (the debugger port, 1044, or 1045 with
ad1remoteport turned on at the machine). Installing only this package is
the remote-operator setup -- SDL2 and nothing else from us, no emulator,
no panel code, no tools:

    t30dpy <host>        # SDL2 window, screen 0; -p for another
    tapevis -h <host>    # network reader and punch
    ad1 ...              # see the documentation

t30dpy with no arguments connects to the local machine; its settings come
from ~/.t30dpy.config, then from /etc/pidp1-mods/t30dpy.config when the
main package is installed too.

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
cp -a Am1Includes MacroIncludes Docs Drums Microtapes Diagnostics \
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
# the hardware test program (install/build-all.sh's src/pidp1_test leg). The
# bin/* copy above skips it as an ELF, so name it here as the user command it
# is; its wrapper test.sh travels with the read-only tree (a checkout keeps
# it at the top level) and is symlinked below like the other scripts.
install -m 755 src/pidp1_test/pidp1_test %{buildroot}%{_bindir}/
install -m 755 test.sh $datadir/test.sh
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
ln -s ../share/pidp1-mods/test.sh               %{buildroot}%{_bindir}/pidp1-test

install -m 755 src/pdp1/pdp1                     $libexec/pdp1
install -m 755 src/panel_pidp1/newpanel          $libexec/panel_pidp1
install -m 755 src/vpanel_pdp1/panel_pdp1        $libexec/vpanel_pdp1
install -m 755 src/pdp1_periph/pdp1_periph       $libexec/
install -m 755 src/pdp1_periph/pdp1_periphES     $libexec/
install -m 755 src/usb_paper_tape/pdp1_usb_monitor $libexec/
install -m 755 src/ptytools/mkptyfio src/ptytools/mkptyfl $libexec/
install -m 755 web_pdp1/pdpsrv                   $libexec/
# pdp1.service's screen wrappers (ExecStart/ExecStop), and pidp1-attach,
# the sudoers fragment's target for the group's console; see the comments in
# them and in the unit for why systemd needs a bin_t script in between and
# why the session has a socket directory of its own
install -m 0755 packaging/systemd/libexec/pidp1-screen $libexec/
install -m 0755 packaging/systemd/libexec/pidp1-stop   $libexec/
install -m 0755 packaging/systemd/libexec/pidp1-attach $libexec/

mkdir -p $iotdir
install -m 755 IOTs/*.so $iotdir/

# ---------------------------------------------------------------------------
# Configuration and state. The writable bits are group pidp1 (created by
# the sysusers fragment in %%pre) so a panel driver started by any member can
# write them. The tmpfiles fragment (Source2) recreates the state directories;
# %%post seeds the drum image once. The tape library and boot configurations
# are package content that the machine reads from the state tree, so they
# install there and the package owns them as %%config(noreplace) data -- no
# seeding copy; %%files spells the flags.
# ---------------------------------------------------------------------------
mkdir -p %{buildroot}%{_sysconfdir}/pidp1-mods
cp -a pidp1.config.example    %{buildroot}%{_sysconfdir}/pidp1-mods/pidp1.config
cp -a t30dpy.config.example   %{buildroot}%{_sysconfdir}/pidp1-mods/t30dpy.config
cp -a microtapes.txt.example  %{buildroot}%{_sysconfdir}/pidp1-mods/microtapes.txt
cp -a bin/usb_paper_tape_ports.cfg %{buildroot}%{_sysconfdir}/pidp1-mods/

mkdir -p -m 775 $statedir $statedir/tapes $statedir/bootcfg
# the shipped library (9.4M of tapes, bootcfg/<number>.cfg files). What rpm
# records is decided entirely by the %%attr in %%files (0664 root:pidp1
# data, 0775 subdirectories, 2775 top ones); these chmods just normalize the
# cp -a'd tree so the buildroot matches.
cp -a tapes/. $statedir/tapes/
cp -a bootcfg/. $statedir/bootcfg/
find $statedir/tapes $statedir/bootcfg -type d -exec chmod 755 {} +
find $statedir/tapes $statedir/bootcfg -type f -exec chmod 0644 {} +

# ---------------------------------------------------------------------------
# Man pages for the front doors, desktop entries, and their theme icons (the
# same hicolor names install.sh creates in the user's theme for a checkout).
# ---------------------------------------------------------------------------
install -Dm 0644 man/pdp1.1 %{buildroot}%{_mandir}/man1/pdp1.1
install -Dm 0644 man/pdp1control.1 %{buildroot}%{_mandir}/man1/pdp1control.1
install -Dm 0644 man/pidp1-test.1 %{buildroot}%{_mandir}/man1/pidp1-test.1

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

# The OS-integration fragments, so a checkout and the build see one copy
install -Dm 0644 %{SOURCE1} %{buildroot}%{_sysusersdir}/pidp1-mods.conf
install -Dm 0644 %{SOURCE2} %{buildroot}%{_tmpfilesdir}/pidp1-mods.conf
# the udev rule that hands the panel's GPIO chip (and gpiomem, for the
# register backend) to the pidp1 group; zz-* so it loads after the 99-* rules
# the sibling cabinets ship for the same controller (see the rule's header).
# It lives under packaging/systemd/ beside its siblings, and Source0 carries
# it into the build
install -Dm 0644 packaging/systemd/udev.d/zz-pidp1-mods.rules \
    %{buildroot}%{_udevrulesdir}/zz-pidp1-mods.rules
# The boot-time units and their preset. All three live under
# packaging/systemd/ beside the fragments above and ride in Source0; the
# preset disables them so an install stays opt-in (systemd's preset policy
# without a preset file is to enable).
install -Dm 0644 packaging/systemd/system/pdp1.service \
    %{buildroot}%{_unitdir}/pdp1.service
install -Dm 0644 packaging/systemd/system/pdp1-panel.service \
    %{buildroot}%{_unitdir}/pdp1-panel.service
install -Dm 0644 packaging/systemd/system/pdp1-bootcfg.service \
    %{buildroot}%{_unitdir}/pdp1-bootcfg.service
install -Dm 0644 packaging/systemd/system-preset/90-pidp1-mods.preset \
    %{buildroot}%{_presetdir}/90-pidp1-mods.preset

# The opt-in firewalld services. Nothing opens at install time -- these are
# here so enabling remote use is one firewall-cmd --add-service per feature
# instead of six --add-port lines (see the port table in packaging/README.md).
# /usr/lib/firewalld/services is where firewalld finds system-shipped
# definitions; the package must not own or touch the running configuration.
install -Dm 0644 packaging/firewalld/pidp1-mods.xml \
    %{buildroot}%{_prefix}/lib/firewalld/services/pidp1-mods.xml
install -Dm 0644 packaging/firewalld/pidp1-mods-debug.xml \
    %{buildroot}%{_prefix}/lib/firewalld/services/pidp1-mods-debug.xml

# The console attach: members of the pidp1 group may sudo -u pidp1 the
# two pidp1-attach forms that look at and join the session the service owns.
# The noreplace config mark (see %%files) is how Fedora packages ship a
# sudoers entry a site may want to edit: site edits survive upgrades and
# the shipped file lands as .rpmnew.
install -Dm 0440 packaging/pidp1-mods.sudoers \
    %{buildroot}%{_sysconfdir}/sudoers.d/pidp1-mods

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
%systemd_post pdp1.service pdp1-panel.service pdp1-bootcfg.service
%tmpfiles_create_package %{name} %{SOURCE2}
st=%{_sharedstatedir}/pidp1-mods
da=%{_datadir}/pidp1-mods
# seed once; never overwrite what the site already put in the state directory
if [ ! -f $st/pdp23drum ]; then
    cp -a $da/pdp23drum.example $st/pdp23drum
    chgrp pidp1 $st/pdp23drum
    chmod 0664 $st/pdp23drum
fi
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor 2>/dev/null || :
# re-apply the shipped rule to the panel nodes so an existing cabinet does
# not wait for a reboot (no-op where neither node family exists)
udevadm control --reload-rules 2>/dev/null || :
for d in /dev/gpiomem* /dev/gpiochip*; do
    [ -e "$d" ] && udevadm trigger -c add "$d" 2>/dev/null || :
done

%preun
%systemd_preun pdp1.service pdp1-panel.service pdp1-bootcfg.service

%postun
%systemd_postun_with_restart pdp1.service pdp1-panel.service pdp1-bootcfg.service
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor 2>/dev/null || :
udevadm control --reload-rules 2>/dev/null || :

%files
%license LICENSE
%license %{_prefix}/share/licenses/%{name}/LICENSE.gorilla-websocket
%doc README.md RELEASENOTES.txt PACKAGING.md
%{_mandir}/man1/pdp1.1*
%{_mandir}/man1/pdp1control.1*
%{_mandir}/man1/pidp1-test.1*
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
%{_bindir}/pidp1-test
%{_bindir}/pidp1_test
%{_bindir}/scanpf
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
%{_datadir}/pidp1-mods/src
%{_datadir}/pidp1-mods/web_pdp1
%{_datadir}/pidp1-mods/pdp23drum.example
%{_datadir}/pidp1-mods/pidp1.config.example
%{_datadir}/pidp1-mods/test.sh
%dir %attr(2775, root, pidp1) %{_datadir}/pidp1-mods/Microtapes
%attr(0664, root, pidp1) %{_datadir}/pidp1-mods/Microtapes/*
%dir %attr(2775, root, pidp1) %{_datadir}/pidp1-mods/Drums
%attr(0664, root, pidp1) %{_datadir}/pidp1-mods/Drums/*
%{_sysusersdir}/pidp1-mods.conf
%{_tmpfilesdir}/pidp1-mods.conf
%{_udevrulesdir}/zz-pidp1-mods.rules
%attr(0440, root, root) %config(noreplace) %{_sysconfdir}/sudoers.d/pidp1-mods
%{_unitdir}/pdp1.service
%{_unitdir}/pdp1-panel.service
%{_unitdir}/pdp1-bootcfg.service
%{_presetdir}/90-pidp1-mods.preset
%{_prefix}/lib/firewalld/services/pidp1-mods.xml
%{_prefix}/lib/firewalld/services/pidp1-mods-debug.xml
%{_datadir}/applications/audioOff.desktop
%{_datadir}/applications/audioOn.desktop
%{_datadir}/applications/pdp1central.desktop
%{_datadir}/applications/pdp1control.desktop
%{_datadir}/applications/pdp1startup.desktop
%{_datadir}/applications/ptp.desktop
%{_datadir}/applications/ptr.desktop
%{_datadir}/applications/tty.desktop
%{_datadir}/icons/hicolor/scalable/apps/pdp1.svg
%{_datadir}/icons/hicolor/scalable/apps/pdp1central.svg
%{_datadir}/icons/hicolor/scalable/apps/pdp1control.svg
%{_datadir}/icons/hicolor/scalable/apps/pidp1-ptp.svg
%{_datadir}/icons/hicolor/scalable/apps/pidp1-ptr.svg
%{_datadir}/icons/hicolor/scalable/apps/soroban.svg
%config(noreplace) %{_sysconfdir}/pidp1-mods/usb_paper_tape_ports.cfg
# writable-by-group: the members of pidp1 run the machine. tapes/ and
# bootcfg/ are the shipped library itself: package-owned content in the state
# tree, marked %%config(noreplace) -- a site that patches a bootcfg or a tape
# keeps its copy across upgrades (the new shipped one arrives as .rpmnew),
# and files the site adds itself rpm never touches.
#
# Every path below is matched by exactly one line, which is not paranoia but
# the lesson of a probe: rpm's * does not cross a slash, a bare glob that
# matches a directory inherits its mode AND recurses into its contents, and
# overlapping %%config entries record the wrong mode with "File listed
# twice" -- which line wins is not a thing to build on. So: directories get
# %%dir lines, the top-level library files are the ones with a dot in the
# name (none without, and no directory has one), the subdirectories'
# contents one level down get */*. Add a %%dir line when the library grows a
# sixth curated subdirectory.
%dir %attr(2775, root, pidp1) %{_sharedstatedir}/pidp1-mods
%dir %attr(2775, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes
%dir %attr(0775, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes/doc
%dir %attr(0775, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes/flap
%dir %attr(0775, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes/music
%dir %attr(0775, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes/old
%dir %attr(0775, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes/sources
%config(noreplace) %attr(0664, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes/*.*
%config(noreplace) %attr(0664, root, pidp1) %{_sharedstatedir}/pidp1-mods/tapes/*/*
%dir %attr(2775, root, pidp1) %{_sharedstatedir}/pidp1-mods/bootcfg
%config(noreplace) %attr(0664, root, pidp1) %{_sharedstatedir}/pidp1-mods/bootcfg/*
%dir %attr(2775, root, pidp1) %{_sysconfdir}/pidp1-mods
%attr(0664, root, pidp1) %config(noreplace) %{_sysconfdir}/pidp1-mods/pidp1.config
%attr(0664, root, pidp1) %config(noreplace) %{_sysconfdir}/pidp1-mods/microtapes.txt

# The network clients share one package because they share one reason to
# exist -- a machine that talks to a pdp1 elsewhere -- and one dependency
# story: SDL2 for the two windows, nothing extra for ad1. Per-tool packages
# would each cost a debuginfo and a version pin to say "I do not want SDL2".
# Everything that draws t30dpy travels together: the desktop entry names
# Icon=t30dpy, so the svg follows the .desktop file. The /etc default
# travels too (t30dpy reads ~/.t30dpy.config first and this file second,
# t30dpy.c's config comment) but stays plain root:root unlike its /etc
# siblings: a group there would become Requires group(pidp1-mods), which
# only the main package provides -- and a dependency that drags the
# emulator onto the remote machine is exactly what this package exists to
# avoid. Cabinet operators who want it group-writable have
# ~/.t30dpy.config, and remote operators always do.
%files clients
%license LICENSE
%doc t30dpy.config.example
%{_bindir}/ad1
%{_bindir}/tapevis
%{_bindir}/t30dpy
%{_datadir}/applications/t30dpy.desktop
%{_datadir}/icons/hicolor/scalable/apps/t30dpy.svg
%config(noreplace) %{_sysconfdir}/pidp1-mods/t30dpy.config

%changelog
* Wed Nov 25 2026 Dennis Gilmore <dennis@ausil.us> - 1.0-5.20261125
- pdp1.service starts again: screen died at once with "Directory
  '/run/screen' must have mode 777". NoNewPrivileges= suppresses screen's
  setgid bit, and without that egid screen insists on 0777 for the screen
  RPM's 0775 root:screen /run/screen - the group list does not count. The
  session now lives in its own socket directory, /run/pidp1/screen (0700
  pidp1, tmpfiles), pinned in all three wrappers. The console attach moves
  with it: sudoers allows the new pidp1-attach wrapper (which pins
  SCREENDIR, since sudo's env_reset drops it) instead of a bare screen -x
  that looked in /run/screen and found nothing, with use_pty so screen as
  pidp1 can open the terminal.
- libgpiod backend: PIDP1_GPIO_CHIP no longer overflows the 64-byte path
  buffer; gpio_get_level no longer flips a held output line to input (v2
  reads outputs fine, and the register backend never changes direction on
  a read); gpio_set/gpio_clear make the line an output, as the register
  backend's do.
- The panel driver no longer exits silently under an upstream device tree
  (Fedora's kernel on a Pi 5): gpiolib_init() counted GPIOs only by
  walking /aliases/gpioN, which only Raspberry Pi device trees carry, so
  it returned 0 and initGPIO() gave up although libgpiod had already
  claimed the RP1. The gpiod chip's line count stands in now, both
  failure paths say what failed, and PIDP1_GPIO_VERBOSE=1 shows the
  chip probe.

* Wed Nov 25 2026 Dennis Gilmore <dennis@ausil.us> - 1.0-4.20261125
- The panel's libgpiod backend actually drives the panel now (the pidp8i
  packaging's fixup patch is the reference for all four defects):
  auto-select matched chip names as *substrings*, so on a Pi 5 the probe
  claimed one of the 32-line brcmstb-gpio blocks ahead of the header -
  "brcm" is a substring - and the panel drove a dead controller even as
  root; direction/pull changes release-then-re-requested a line this
  process still held, which the kernel refuses with EBUSY (reconfigure in
  place is the only legal way, and it also closes the glitch window); every
  line was requested with bias DISABLED, destroying the firmware's
  power-on pull-ups so all buttons read released (bias is AS_IS unless
  gpio_set_pull asked otherwise); get_level sampled lines still held as
  outputs and set_drive force-flipped columns to outputs, breaking the
  register backend's blank-to-input matrix pattern. PIDP1_GPIO_CHIP now
  also accepts a chip name (pinctrl-rp1), requests carry the "pidp1"
  consumer for gpioinfo, and a permission-refused probe says so.

* Wed Nov 25 2026 Dennis Gilmore <dennis@ausil.us> - 1.0-3.20261125
- The operator group and the service account are both the literal pidp1,
  matching the cabinet host's existing group: one sysusers line creates the
  group and the user with it as primary (a GIDNAME in a u line's second
  column parses only as "-" or a number - it died on aset that way), and
  the udev rule, the tmpfiles and the group-attr'd state tree,
  /etc/pidp1-mods and the units all key off it; operators are
  usermod -aG pidp1. The rule installs as zz-pidp1-mods.rules so it loads
  after the 99-* rules the PiDP-10/PiDP-11 packaging ships for the same
  RP1/bcm2835 controller - a node has one group and the last match wins
  (pidp10's rule was taking the Pi 5 header chip under both).
- The console is shared by the group: pdp1.service now runs the engine in a
  detached screen session named pidp1 (new pidp1-screen/pidp1-stop
  wrappers, SupplementaryGroups=screen, the SELinux and setgid reasons in
  the unit's comments), /etc/sudoers.d/pidp1-mods lets pidp1 members
  `sudo -u pidp1 screen -ls/-x pidp1`, and `pdp1` with no arguments
  falls back to that session.
- The panel test program is finally in the RPM - the bin/* copy skipped it
  as an ELF: /usr/bin/pidp1_test, test.sh as /usr/bin/pidp1-test with a man
  page, and test.sh starts the panel driver unprivileged for pidp1 members.

* Sat Nov 21 2026 Dennis Gilmore <dennis@ausil.us> - 1.0-2.20261121
- The servers listen on IPv6, and on IPv4 through it: one dual-family
  socket per port (IPV6_V6ONLY off), with the IPv4-only socket kept as
  the fallback for kernels with IPv6 disabled. Covers pdp1's ports, the
  typewriter, the peripheral port and tapevis through common.c's
  listenQuietly(); ad1server's listeners bind the same way, so the local
  debugger port stays loopback-only in either family. telnet localhost
  and [::1] now reach the console directly. Release 2 of today's
  snapshot for the re-upload.

* Sat Nov 21 2026 Dennis Gilmore <dennis@ausil.us> - 1.0-1.20261121
- tapes/ and bootcfg/ moved from /usr/share to /var/lib/pidp1-mods, as
  %%config(noreplace) package content: site edits survive upgrades (the
  shipped update lands as .rpmnew) and the shipped library is group-owned
  by pidp1-mods (0664 data, 0775 subdirectories, 2775 top) so operators
  in the group can curate it without root.
- New pidp1-mods-clients subpackage: t30dpy, tapevis and ad1 -- the
  programs that talk to a pdp1 over the network -- for machines that
  watch or debug a remote machine. SDL2 and glibc are its only runtime
  deps; the main package Recommends it, so cabinet installs are unchanged.
- IOTs/cleanall.sh gained the shebang whose absence failed the emulated
  riscv64 build (exit 127 under qemu-user's direct exec).

* Sun Nov 15 2026 Dennis Gilmore <dennis@ausil.us> - 1.0-1.20261115
- Initial packaged layout: FHS homes per src/common/pidp1_paths.h and
  bin/pidp1-env.sh, one build list in install/build-all.sh, sysusers and
  tmpfiles for the pidp1-mods group and state, desktop entries, hicolor
  icons, man pages for pdp1 and pdp1control.
