#!/bin/bash
#
# pdp1: with no arguments, bring the user into the running simulator's screen session
# (Ctrl-A d leaves it again); with one, start a front-end program beside it.
#
# 15-Nov-2026 wje locations from bin/pidp1-env.sh, and the Teletype's path is a setting.

. "${PIDP1_ENV:-$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/pidp1-env.sh}"

if [ $# -eq 0 ]; then

	procs=`screen -ls pidp1 | grep -E '[0-9]+\.pidp1' | wc -l`
	echo $procs
	if [ $procs -ne 0 ]; then
		screen -Dr pidp1
	fi

else
	case $1 in
		con)
			# The noisy Teletype model 33 is the PiDP-10 project's 'sty', a separate
			# install; PIDP10_STY points at it. Without it, use 'pdp1 soroban'.
			sty="${PIDP10_STY:-/opt/pidp10/bin/sty}"
			if [ ! -x "$sty" ]; then
				echo "no Teletype emulator at $sty: set PIDP10_STY, or use pdp1 soroban" >&2
				exit 1
			fi
			nohup "$sty" -e telnet localhost 1025 > /dev/null 2>&1 &
			;;
		soroban)
			nohup lxterminal --command="telnet localhost 1041" > /dev/null 2>&1 &
			;;
		ptr)
			nohup "$PIDP1_SCRIPTS/load_ptr.sh" > /dev/null 2>&1 &
			;;
		ptp)
			nohup "$PIDP1_SCRIPTS/save_ptp.sh" > /dev/null 2>&1 &
			;;
		tape)
			nohup "$PIDP1_BINDIR/tapevis" > /dev/null 2>&1 &
			;;
		*)
			echo options are: 
			echo  [soroban ptr ptp tape]
			echo when run without options, 
			echo  pdp1 brings you into the simulator - Ctrl-A d to leave
			;;
	esac
fi
