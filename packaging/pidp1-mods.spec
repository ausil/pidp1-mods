# pidp1-mods.spec -- Fedora-style RPM for the PiDP-1 simulator tree.
#
# The layout is the one src/common/pidp1_paths.h and bin/pidp1-env.sh describe; they
# must agree with the %files list below:
#
#   /usr/share/pidp1-mods    read-only program data, a mirror of the checkout: the tape
#                            library, Microtapes, Drums, Am1Includes, Docs, FunStuff,
#                            the web assets, and bin/ with the helper scripts.
#   /var/lib/pidp1-mods      what the running machine writes: the Type 23 drum image,
#                            coremem, punch.out, and tapes/ and bootcfg/, seeded on
#                            first install from the read-only masters above.
#   /etc/pidp1-mods          the site's configuration: pidp1.config, t30dpy.config,
#                            microtapes.txt, usb_paper_tape_ports.cfg.
#   /usr/lib/pidp1-mods/IOTs the dynamic IOT plugins the emulator dlopen()s by absolute
#                            path -- plain /usr/lib, not the multilib /usr/lib64, so
#                            one value works on every architecture (it is not part of
#                            the system library path anyway).
#   /usr/libexec/pidp1-mods  the programs the scripts start rather than users type.
#   /usr/bin                 the user commands, matching the checkout install's
#                            /usr/local/bin set.
#
# Everyone who runs the emulator needs to be a member of the pidp1-mods group: the
# drum image, the state directories, /etc/pidp1-mods (pdp1central edits pidp1.config),
# and the writable Microtapes/ and Drums/ under the data directory are group-writable.
#
# Build it from a checkout (builds only; nothing is installed on the build machine):
#
#   v=0.$(date +%Y%m%d)
#   mkdir -p rpmbuild/{BUILD,RPMS,SPECS,SOURCES,BUILDROOT}
#   git archive --prefix=pidp1-mods-$v/ --format=tar HEAD | \
#       gzip > rpmbuild/SOURCES/pidp1-mods-$v.tar.gz
#   sed -i "s/^Version:.*/Version: $v/" packaging/pidp1-mods.spec   # or -D "version $v"
#   rpmbuild --define '_topdir %(pwd)/rpmbuild' -bb packaging/pidp1-mods.spec
#
# The hardware front panel driver is shipped without the setuid bit; a machine with a
# real PiDP-1 panel should run src/panel_pidp1/setpriv.sh on the installed binary, or
# wait for the libgpiod plus udev-rule route.

%global debug_package %{nil}

Name:           pidp1-mods
Version:        0.20261115
Release:        1%{?dist}
Summary:        PDP-1 simulator, PiDP-1 panel drivers, assembler and tools
License:        MIT
URL:            https://github.com/ausil/pidp1-mods
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  gcc make flex bison zlib-devel desktop-file-utils
BuildRequires:  pkgconfig(sdl2) pkgconfig(SDL2_image) pkgconfig(SDL2_ttf)
BuildRequires:  golang

Requires:       nmap-ncat screen zenity python3 python3-tk lxterminal telnet
Recommends:     golang
Requires(pre):  shadow-utils

%description
A PDP-1 emulator with the PiDP-1 physical and virtual front panels, the Type 23
drum and Type 550 microtape IOTs, the am1 macro assembler, the ad1 debugger, the
t30dpy Type 30 display, and the rest of the pdp1 / pdp1control / pdp1central
tool set. The FHS layout matches src/common/pidp1_paths.h and bin/pidp1-env.sh,
so a packaged install and a source checkout behave the same.

%prep
%setup -q

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

# bin/ keeps only the scripts: pdp1central runs bin/pdp1control.sh, bin/askfile and
# bin/save_ptp.sh from here, and the scripts themselves source pidp1-env.sh.
mkdir -p $datadir/bin
for f in bin/*; do
    if [ -f "$f" ] && ! head -c 4 "$f" | grep -q ELF; then
        cp -a "$f" $datadir/bin/
    fi
done

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
install -m 755 bin/pdp1.sh %{buildroot}%{_bindir}/pdp1
install -m 755 bin/pdp1control.sh %{buildroot}%{_bindir}/pdp1control
# the dialogs and fiodec helpers, typed by pdp1central and by people. The
# wrappers find their Python siblings beside themselves, so both go in.
install -m 755 bin/tkaskopenfile bin/tkaskopenfilewrite \
               bin/encode_fiodec bin/decode_fiodec bin/tape_visualizer \
               bin/encode_fiodec.py bin/decode_fiodec.py bin/tape_visualizer.py \
               %{buildroot}%{_bindir}/
# sourced, not run: the /usr/bin copies of pdp1.sh and pdp1control.sh look for it
# beside themselves, which is how bin/pidp1-env.sh says scripts find it.
install -m 644 bin/pidp1-env.sh %{buildroot}%{_bindir}/

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

# ---------------------------------------------------------------------------
# Configuration and state. The writable bits are group pidp1-mods so a panel
# driver started by any member can write them: pdp1central saves pidp1.config,
# the microtape IOT writes tape images under Microtapes/, the Type 23 drum is
# a file in the state directory, and FunStuff assembly happens under FunStuff.
# ---------------------------------------------------------------------------
mkdir -p %{buildroot}%{_sysconfdir}/pidp1-mods
cp -a pidp1.config.example    %{buildroot}%{_sysconfdir}/pidp1-mods/pidp1.config
cp -a t30dpy.config.example   %{buildroot}%{_sysconfdir}/pidp1-mods/t30dpy.config
cp -a microtapes.txt.example  %{buildroot}%{_sysconfdir}/pidp1-mods/microtapes.txt
cp -a bin/usb_paper_tape_ports.cfg %{buildroot}%{_sysconfdir}/pidp1-mods/

mkdir -p -m 775 $statedir $statedir/tapes $statedir/bootcfg

# ---------------------------------------------------------------------------
# Desktop entries and their theme icons (the same copies install.sh makes
# into ~/.local/share/icons for a checkout).
# ---------------------------------------------------------------------------
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

%pre
getent group pidp1-mods >/dev/null || groupadd -r pidp1-mods

%post
st=%{_sharedstatedir}/pidp1-mods
da=%{_datadir}/pidp1-mods
if [ ! -f $st/pdp23drum ]; then
    cp -a $da/pdp23drum.example $st/pdp23drum
    chgrp pidp1-mods $st/pdp23drum
    chmod 0664 $st/pdp23drum
fi
# seed the writable tape library and boot configurations from the read-only
# masters, never overwriting what the site already put there
cp -aN $da/tapes/.   $st/tapes/   2>/dev/null || :
cp -aN $da/bootcfg/. $st/bootcfg/ 2>/dev/null || :
# the microtape IOT writes images under Microtapes/, and the drum tools put
# images under Drums/, so those two data subdirectories are group-writable
# (kept out of %files so the recursive data entry and these do not clash)
for d in $da/Microtapes $da/Drums; do
    chgrp -R pidp1-mods $d 2>/dev/null || :
    chmod -R g+w $d 2>/dev/null || :
    chmod g+s $d 2>/dev/null || :
done
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor 2>/dev/null || :

%postun
gtk-update-icon-cache -qf %{_datadir}/icons/hicolor 2>/dev/null || :

%files
%license LICENSE
%doc README.md RELEASENOTES.txt
%{_bindir}/ad1
%{_bindir}/am1
%{_bindir}/asr33tape
%{_bindir}/decode_fiodec
%{_bindir}/decode_fiodec.py
%{_bindir}/disassemble
%{_bindir}/docviewer
%{_bindir}/drumlist
%{_bindir}/drumupdater
%{_bindir}/encode_fiodec
%{_bindir}/encode_fiodec.py
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
%{_bindir}/pidp1-env.sh
%{_bindir}/scanpf
%{_bindir}/t30dpy
%{_bindir}/tapevis
%{_bindir}/tape_visualizer
%{_bindir}/tape_visualizer.py
%{_bindir}/tkaskopenfile
%{_bindir}/tkaskopenfilewrite
%{_libexecdir}/pidp1-mods/
%{_prefix}/lib/pidp1-mods/
%{_datadir}/pidp1-mods/
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
* Sat Nov 15 2026 Dennis Gilmore <dennis@ausil.us> - 0.20261115-1
- Initial packaged layout: FHS homes per src/common/pidp1_paths.h, single
  build list in install/build-all.sh, desktop entries and hicolor icons.
