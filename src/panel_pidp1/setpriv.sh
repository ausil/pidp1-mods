#!/bin/bash
#
# Give the hardware panel driver its privileges, the checkout-install equivalent of what
# install.sh does for bin/panel_pidp1: setuid for the GPIO pins, and the option of running
# as a real-time thread. Works on this checkout wherever it lives.
#
# This is only needed for the register backend's /dev/mem fallback. newpanel
# now prefers the libgpiod backend: where it can claim the Pi's gpiochip -
# packaged installs ship zz-pidp1-mods.rules and cabinet users are in the
# pidp1 group - the driver runs unprivileged and setuid root, and this
# script is not needed. A bare checkout has neither the group nor the rule
# installed, which is why it still calls for them.

here="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
sudo chmod +s "$here/newpanel"
sudo setcap cap_sys_nice+ep "$here/newpanel"
