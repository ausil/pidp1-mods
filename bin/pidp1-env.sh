# pidp1-env.sh -- where the scripts find everything. Sourced, never run.
#
# The tree used to be a checkout that had to live in /opt/pidp1-mods, with that path written
# out in a dozen scripts. Installed as an RPM the pieces go to their normal FHS homes, and
# this is the one place that says where. src/common/pidp1_paths.h holds the same map for the
# compiled programs; the two must agree.
#
# Every value is an environment override first, so a build tree, a chroot or a test points
# the whole script set somewhere else without anything being edited:
#
#       PIDP1_STATEDIR=/tmp/pdp1test pdp1control start
#
# Scripts reach this file with
#
#       . "${PIDP1_ENV:-<their own directory>/pidp1-env.sh}"
#
# so it must not run anything, print anything, or touch the exit status.

# An uninstalled build tree: this file in bin/, the sources one level up. Everything then
# lives under one root, the way it always has, and the compiled programs are the ones make
# just left there.
pidp1_here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$pidp1_here/../src/pdp1" ] && [ -d "$pidp1_here/../IOTs" ]; then
    pidp1_installed=0
else
    pidp1_installed=1
fi

: "${PIDP1_ROOT:=$([ $pidp1_installed -eq 0 ] && cd "$pidp1_here/.." && pwd || echo /usr/share/pidp1-mods)}"

# Read-only program data: Microtapes, the Am1 include files, the web assets,
# and the helper scripts the front ends run. (The tape library and bootcfg/
# are NOT here: they live in PIDP1_STATEDIR, where the machine reads them.)
: "${PIDP1_DATADIR:=$PIDP1_ROOT}"
# What the running machine writes: the Type 23 drum image, coremem, punch.out, and tapes/,
# the tape library the front panel selector boots from. The emulator is started with this as
# its working directory, which is where punch.out and coremem end up.
: "${PIDP1_STATEDIR:=$( [ $pidp1_installed -eq 0 ] && echo "$PIDP1_ROOT" || echo /var/lib/pidp1-mods)}"
# The site's configuration: pidp1.config, t30dpy.config, microtapes.txt, the USB port map.
: "${PIDP1_SYSCONFDIR:=$( [ $pidp1_installed -eq 0 ] && echo "$PIDP1_ROOT" || echo /etc/pidp1-mods)}"
# The dynamic IOT plugins the emulator dlopen()s.
: "${PIDP1_IOTDIR:=$( [ $pidp1_installed -eq 0 ] && echo "$PIDP1_ROOT/IOTs" || echo /usr/lib/pidp1-mods/IOTs)}"
# The emulator, the panel drivers and the peripheral simulators: started by these scripts and
# by the desktop entries, not typed by a user.
: "${PIDP1_LIBEXECDIR:=$( [ $pidp1_installed -eq 0 ] && echo "$PIDP1_ROOT/bin" || echo /usr/libexec/pidp1-mods)}"
# The commands a user types.
: "${PIDP1_BINDIR:=$( [ $pidp1_installed -eq 0 ] && echo "$PIDP1_ROOT/bin" || echo /usr/bin)}"

# Where the scripts put what they write for one user, rather than for the machine: the
# pdp1control start-time choices. t30dpy already keeps ~/.t30dpy.config for the same reason.
: "${XDG_CONFIG_HOME:=$HOME/.config}"
: "${PIDP1_USERCONF:=$XDG_CONFIG_HOME/pidp1-mods}"

# The names the scripts actually use, so that the layout above is spelled once.
PIDP1_TAPES="$PIDP1_STATEDIR/tapes"          # what PDP1_DIR/tapes means in bootcfg/*.cfg
PIDP1_BOOTCFG="$PIDP1_STATEDIR/bootcfg"      # the per-selector boot configurations
PIDP1_SCRIPTS="$PIDP1_DATADIR/bin"           # pdp1ctl, load_ptr.sh, save_ptp.sh, the dialogs
PIDP1_WEB="$PIDP1_DATADIR/web_pdp1"          # the browser front end's assets
PIDP1_CONTROL_CONFIG="$PIDP1_USERCONF/pdp1control.config"

export PIDP1_ROOT PIDP1_DATADIR PIDP1_STATEDIR PIDP1_SYSCONFDIR PIDP1_IOTDIR
export PIDP1_LIBEXECDIR PIDP1_BINDIR PIDP1_USERCONF
export PIDP1_TAPES PIDP1_BOOTCFG PIDP1_SCRIPTS PIDP1_WEB PIDP1_CONTROL_CONFIG

unset pidp1_here pidp1_installed
