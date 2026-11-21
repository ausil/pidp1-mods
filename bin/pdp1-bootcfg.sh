#!/bin/bash
#
# pdp1-bootcfg: feed pdp1 its boot configuration, the way pdp1control start
# does, for the packaged boot-time units (pdp1-bootcfg.service).
#
# The boot number, octal, names bootcfg/<number>.cfg in the state directory.
# It comes from PDP1_BOOT_NUMBER when set (set it with a unit drop-in or in
# the environment), and from the panel's sense switches (scanpf) otherwise.
# A cabinet with no panel sees the switches all down (0), and with no 0.cfg
# the machine comes up idle -- the same forgiving behavior pdp1control has.
#
# The boot images themselves need no fetching: the package installs tapes/
# and bootcfg/ under $PIDP1_STATEDIR directly.

. "${PIDP1_ENV:-$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/pidp1-env.sh}"

sw="${PDP1_BOOT_NUMBER}"
if [ -z "$sw" ]; then
	# scanpf reports the sense switches' value, and 0 with no panel attached.
	"$PIDP1_BINDIR/scanpf" >/dev/null 2>&1
	sw=$(printf "%o" $?)
fi

cfg="$PIDP1_BOOTCFG/${sw}.cfg"
if [ ! -r "$cfg" ]; then
	echo "pdp1-bootcfg: no boot configuration $cfg, nothing loaded"
	exit 0
fi

# The command ports belong to pdp1; wait, at most 5 seconds, for 1040 rather
# than race the engine's startup.
for _ in $(seq 50); do
	ncat -z -w 1 localhost 1040 2>/dev/null && break
	sleep 0.1
done

echo "pdp1-bootcfg: boot number $sw"
cat "$cfg" | "$PIDP1_SCRIPTS/pdp1ctl"
