#!/bin/bash
#
# Give the hardware panel driver its privileges, the checkout-install equivalent of what
# install.sh does for bin/panel_pidp1: setuid for the GPIO pins, and the option of running
# as a real-time thread. Works on this checkout wherever it lives. The packaged version
# leaves this to the administrator; the eventual fix is libgpiod plus a udev rule, after
# which neither is needed.

here="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
sudo chmod +s "$here/newpanel"
sudo setcap cap_sys_nice+ep "$here/newpanel"
