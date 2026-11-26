#!/bin/bash
#
# Drive the PiDP-1 hardware front panel by hand: a light sweep, then the switches, then the
# joystick, so dead lamps and stuck switches can be found without a simulator running.
# The panel driver is started here rather than by pdp1control, and the test owns it.
#
# 15-Nov-2026 wje locations from bin/pidp1-env.sh.

. "${PIDP1_ENV:-$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/bin/pidp1-env.sh}"

echo Starting PiDP-1 test program
echo
echo stopping pdp-1 simulation, if it is running...

pdp1control stop

echo ...stopped pdp-1 simulation
sleep 2
echo
echo starting pidp-1 panel driver...

# The driver drives the panel through libgpiod when it can claim the Pi's gpiochip; a
# packaged install ships zz-pidp1-mods.rules and cabinet users are in the pidp1 group,
# which makes that sudo unnecessary there. A bare checkout has neither the group nor the
# rule, so it starts the driver as root. PIDP1_GPIO_CHIP pins the chip by name if a board
# has more than one. (Exact group match: a -w test would also accept pidp1-mods and any
# other group that merely starts with pidp1.)
if id -nG | tr ' ' '\n' | grep -qx pidp1; then
	"$PIDP1_LIBEXECDIR/panel_pidp1"&
else
	sudo "$PIDP1_LIBEXECDIR/panel_pidp1"&
fi

echo ...started panel driver
sleep 1
echo
echo starting test program.
echo "What you should expect:"
echo
echo "Lights: shows a light running across the panel," 
echo "        (including the IO panel lamps if you have them)"
echo "--> check for any dead lamps."
echo
echo "Switches: set all switches to the DOWN position"
echo "          and the three horizontal switches to RIGHT"
echo "          then you should see the output as:" 
echo "          000000 000000 000000 000000"
echo "--> check for all zeros if switches are set to DOWN and RIGHT"
echo
echo "          toggle each switch and see if it changes the output"
echo "--> check that they do. Or, a quicker check is:"
echo
echo "          If all switches are set to UP and LEFT,"
echo "          and you leave the bottom 8 switches untouched, expect"
echo "          777777 777777 776000 000000"
echo "-->quick check for all small switches, but manually test the lower 8"
echo
echo "Joystick test: press each button"
echo "--> check for a change in output"
echo

"$PIDP1_BINDIR/pidp1_test"

echo
echo test program has ended
echo killing the panel driver

pkill panel_pidp1

echo done.
