#!/bin/bash

# start script for pidp1.  
# 7-Apr-26 wje add reload to have the config file reloaded
# 29-Apr-26 wje change reload to use sighup
# 30-Sep-26 wje (Claude) keep the interface, panel and usbtape choices in pdp1control.config
#    instead of rewriting this script; PIDP1_ROOT; stop, reload and reloadpanel act on exact
#    process names; a missing screen or pdp1 stops the script; apps starts t30dpy only, and
#    stop lets t30dpy end on its own when pdp1 goes
# 02-Oct-26 wje (Claude) the t30dpy choice: start t30dpy beside the gui or web front end
# 05-Oct-26 wje (Claude) only one pdp1 runs at a time, stop waits for pdp1 to exit,
#    start refuses while one is already running, restart no longer sleeps
# 07-Nov-26 wje (Claude) the soroban choice: start the Soroban typewriter terminal with web or
#    apps, when there is a desktop
# 26-Nov-26 (Claude) a machine pdp1.service runs is up, not down: stat and the menu say so and
#    how to reach it, and start, stop and restart leave it to systemctl

# Where everything is: see bin/pidp1-env.sh, which the environment overrides. Once installed
# the read-only data (the helper scripts, the web assets) and the writable state (the drum
# image, coremem, punch.out, tapes/, bootcfg/) are no longer the same directory, so paths are
# spelled out below rather than taken relative to one root. 'root' is the state directory:
# pdp1 starts there, and writes its punch.out and coremem into its own directory.
. "${PIDP1_ENV:-$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/pidp1-env.sh}"
root="$PIDP1_STATEDIR"

# The start-time choices are kept in $PIDP1_CONTROL_CONFIG, as name=value lines:
#   interface=web       gui, web or apps
#   frontpanel=virtual  pidp or virtual
#   usbtape=n           y to use the USB ports for the paper tape reader and punch
#   t30dpy=n            y to start t30dpy beside the gui or web front end (apps starts it anyway)
#   soroban=n           y to start the Soroban typewriter terminal (not with gui, which has
#                       the typewriter)
# A missing file or line keeps the default below. The set, panel, usbtape, t30dpy and soroban
# commands write it.
#
# They belong to the user who starts the panel, not to the machine: $PIDP1_STATEDIR is shared
# and not necessarily writable by this user, and two people testing a build should not inherit
# each other's choices.
mkdir -p "$PIDP1_USERCONF" 2>/dev/null
settings="$PIDP1_CONTROL_CONFIG"
interface="web"
frontpanel="virtual"
usb_paper_tape="n"
t30dpy="n"
soroban="n"

argc=$#
pidp1="$PIDP1_LIBEXECDIR/pdp1"
cd "$root" || { echo "cannot use $root, the PiDP-1 state directory" >&2; exit 1; }

# Requires screen utility for detached pidp1 console functionality.
#
if ! test -x /usr/bin/screen; then
	echo "screen not found"
	exit 1
fi
if ! test -x "$pidp1"; then
	echo "$pidp1 not found"
	exit 1
fi

# Read the start-time choices. The file is read line by line, never sourced, so it cannot run
# code. '#' starts a comment; an unknown name or an invalid value keeps the default.
read_settings() {
	test -r "$settings" || return 0
	while IFS= read -r line || [ -n "$line" ]; do
		line="${line%$'\r'}"
		case "$line" in
		''|'#'*) continue ;;
		esac
		name="${line%%=*}"
		value="${line#*=}"
		if [ "$name" = "$line" ]; then
			echo "pdp1control.config: '$line' is not name=value, ignored" >&2
			continue
		fi
		name="${name%"${name##*[![:space:]]}"}"
		value="${value#"${value%%[![:space:]]*}"}"
		value="${value%%[[:space:]]*}"
		case "$name=$value" in
		interface=gui|interface=web|interface=apps)
			interface="$value" ;;
		frontpanel=pidp|frontpanel=virtual)
			frontpanel="$value" ;;
		usbtape=y|usbtape=n)
			usb_paper_tape="$value" ;;
		t30dpy=y|t30dpy=n)
			t30dpy="$value" ;;
		soroban=y|soroban=n)
			soroban="$value" ;;
		interface=*|frontpanel=*|usbtape=*|t30dpy=*|soroban=*)
			echo "pdp1control.config: invalid value '$value' for $name, ignored" >&2 ;;
		*)
			echo "pdp1control.config: unknown setting '$name', ignored" >&2 ;;
		esac
	done < "$settings"
}

# Set one start-time choice in the settings file: every line for the name gets the value,
# or a line is added. The file is written to a temporary name and renamed.
write_setting() {
	temp_file="$settings.tmp"
	if test -f "$settings" && grep -q "^$1[[:space:]]*=" "$settings"; then
		sed "s/^\($1[[:space:]]*=[[:space:]]*\)[^[:space:]]*/\1$2/" "$settings" > "$temp_file" || return 1
	else
		{
			if test -s "$settings"; then
				cat "$settings"
				# the file may not end with a newline
				test -z "$(tail -c 1 "$settings")" || echo
			fi
			echo "$1=$2"
		} > "$temp_file" || return 1
	fi
	mv "$temp_file" "$settings"
}

read_settings

# Check if pidp1 is already running under screen.
#
is_running() {
	procs=`screen -ls pidp1 | grep -E '[0-9]+\.pidp1' | wc -l`
	return $procs
}

# True while pdp1.service runs the machine. Its screen session is the pidp1 account's, in that
# account's own socket directory, so is_running never sees it from any other user; the service
# is asked instead. Such a machine is started and stopped with systemctl, not from here.
service_running() {
	command -v systemctl > /dev/null 2>&1 &&
		systemctl is-active --quiet pdp1.service 2> /dev/null
}

# Say who runs the machine and how to reach it, for a pdp1.service one.
service_note() {
	echo "PiDP-1 is up, run by pdp1.service." >&2
	echo "  pdp1                          attach to its console (Ctrl-A d to leave)" >&2
	echo "  sudo systemctl stop pdp1      stop it (restart, to start it again)" >&2
}

# Refuse start, stop and restart while the service has the machine: a second pdp1 would
# fail, and this user cannot end the service's.
refuse_if_service() {
	if service_running; then
		service_note
		exit 1
	fi
}

# True while any pdp1 process runs, in screen or not. One that has exited but is not yet
# reaped (state Z) holds nothing, so it does not count.
pdp1_running() {
	ps -C pdp1 -o stat= | grep -qv '^Z'
}

do_stat() {
	if service_running; then
		service_note
		status=1
		return $status
	fi
	is_running
	status=$?
	if [ $status -gt 0 ]; then
	    echo "PiDP-1 is up." >&2
	    return $status
	else
	    echo "PiDP-1 is down." >&2
	    return $status
	fi
}

 

# Wait, at most 5 seconds, for pdp1 to listen on the screen-0 display port, 3400: t30dpy gives
# up at once if it cannot connect, and pdp1 starts in screen in the background. Without ss, a
# fixed 5 seconds.
wait_display_port() {
	if ! command -v ss > /dev/null; then
		sleep 5
		return
	fi
	for i in $(seq 50); do
		ss -Htln '( sport = :3400 )' | grep -q . && return
		sleep 0.1
	done
	echo "pdp1 not listening on the display port in 5 seconds; starting t30dpy anyway"
}

# Wait, at most 5 seconds, for a client connected to the screen-0 display port, 3400. Without
# ss, a fixed 3 seconds.
wait_display_client() {
	if ! command -v ss > /dev/null; then
		sleep 3
		return
	fi
	for i in $(seq 50); do
		ss -Htn state established '( dport = :3400 )' | grep -q . && return
		sleep 0.1
	done
	echo "no display client connected in 5 seconds; starting t30dpy anyway"
}

# Start Soroban, the typewriter terminal, with tty.desktop's command. pdp1 serves the
# typewriter, port 1041, to one client at a time, and pdp1_periphES takes it at its start and
# quits without it, so with gui Soroban is not started. Nor is it without a desktop, so this
# script still works where there is none. telnet ends at once if 1041 is not listening, and
# its window would open and close, so Soroban starts only once pdp1 listens, at most 5 seconds.
# Then up to 3 seconds for it to connect, so it is there before the boot program types.
# Without ss, a fixed 2 seconds before and after.
start_soroban() {
	if [ "$interface" = "gui" ]; then
		echo "Soroban not started: the gui has the typewriter"
		return
	fi
	if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
		echo "Soroban not started: no desktop"
		return
	fi
	if ! command -v lxterminal > /dev/null; then
		echo "Soroban not started: lxterminal not found"
		return
	fi
	if command -v ss > /dev/null; then
		for i in $(seq 50); do
			ss -Htln '( sport = :1041 )' | grep -q . && break
			sleep 0.1
		done
		if ! ss -Htln '( sport = :1041 )' | grep -q .; then
			echo "Soroban not started: pdp1 not listening on the typewriter port in 5 seconds"
			return
		fi
	else
		sleep 2
	fi
	echo start Soroban
	nohup lxterminal -e "telnet localhost 1041" > /dev/null 2>&1 &
	if command -v ss > /dev/null; then
		for i in $(seq 30); do
			ss -Htn state established '( dport = :1041 )' | grep -q . && return
			sleep 0.1
		done
		echo "Soroban not connected to the typewriter in 3 seconds"
	else
		sleep 2
	fi
}

do_start() {
	is_running
	if [ $? -gt 0 ]; then
	    echo "PiDP-1 is already running, not starting again." >&2
	    exit 0
	fi
	# Only one pdp1 may run, and one started outside screen is not seen above; a second one
	# would end at once, inside screen where nobody sees why.
	if pdp1_running; then
	    echo "A pdp1 is already running, not starting; pdp1control stop ends it." >&2
	    exit 1
	fi

	echo start panel driver, either virtual or real, depends on the symlink
	if [ "$frontpanel" = "pidp" ]; then
		echo starting PiDP-1 hardware front panel driver
	        nohup "$PIDP1_LIBEXECDIR/panel_pidp1" > /dev/null 2>&1 &
	elif [ "$frontpanel" = "virtual" ]; then
		echo starting on-screen virtual front panel, not PiDP-1 hardware
		echo use
		echo    pdp1control panel pidp
		echo to change that, if you have a PiDP-1!
	        nohup "$PIDP1_LIBEXECDIR/vpanel_pdp1" > /dev/null 2>&1 &
	else
                echo ERROR: NO VALID FRONT PANEL DRIVER, fix with
		echo    pdp1control panel
	fi


	sleep 1 # only needed for autoboot at startup

	echo read boot config from sense switches
	"$PIDP1_BINDIR/scanpf"
	sw=$?

	#sw="${2:-$sw}"
	sw=$(printf "%o" $sw)
	echo switches set to $sw

	echo start pidp1 in screen
	screen -dmS pidp1 "$pidp1"
	status=$?

	if [ "$interface" = "gui" ]; then
		echo start gui peripherals
		sleep 2
		nohup "$PIDP1_LIBEXECDIR/pdp1_periphES" > /dev/null 2>&1 &
	elif [ "$interface" = "web" ]; then
		echo start web server
		cd "$PIDP1_WEB"
		# the installed tree ships the built server; a build tree runs the source
		if [ -x "$PIDP1_LIBEXECDIR/pdpsrv" ]; then
			nohup "$PIDP1_LIBEXECDIR/pdpsrv" > /dev/null 2>&1 &
		else
			nohup go run "$PIDP1_WEB/pdpsrv.go" > /dev/null 2>&1 &
		fi
		cd "$root"
	elif [ "$interface" = "apps" ]; then
		echo start apps
		sleep 1
		echo start "$PIDP1_BINDIR/t30dpy"
		nohup "$PIDP1_BINDIR/t30dpy" >/dev/null 2>&1 &
		# tapevis, the tape reader and punch window, is rarely wanted; run bin/tapevis for it
	fi

	# t30dpy is to have the Type 30 display. pdp1 serves one client per display port, the
	# last to connect, so t30dpy starts after the front end has connected: pdp1_periphES does
	# at its start; pdpsrv only when the browser's display panel opens, and then t30dpy's
	# connection is closed and t30dpy ends.
	if [ "$t30dpy" = "y" ] && [ "$interface" != "apps" ]; then
		wait_display_port
		if [ "$interface" = "gui" ]; then
			wait_display_client
		fi
		echo start "$PIDP1_BINDIR/t30dpy"
		nohup "$PIDP1_BINDIR/t30dpy" >/dev/null 2>&1 &
	fi

	if [ "$soroban" = "y" ]; then
		start_soroban
	fi

	sleep 1 # 0.3
	echo "Configuring PiDP-1 for boot number $sw"
	if ! test -r "$PIDP1_BOOTCFG/${sw}.cfg"; then
		echo "no boot configuration $PIDP1_BOOTCFG/${sw}.cfg, nothing loaded"
	else
		cat "$PIDP1_BOOTCFG/${sw}.cfg" | "$PIDP1_SCRIPTS/pdp1ctl"
	fi

	if [ "$usb_paper_tape" = "y" ]; then
		echo start usb paper tape tool
		nohup "$PIDP1_LIBEXECDIR/pdp1_usb_monitor" > /dev/null 2>&1  &
	fi

	return $status
}

# Signals go by exact process name: a pattern such as 'pdp1$' also matches vpanel_pdp1,
# which has no SIGHUP handler and would end.
do_reload() {
        pkill -x -HUP pdp1
}

do_t30reload() {
        pkill -HUP 't30dpy'
        pkill -HUP 't30dpy3'
}

do_panelreload() {
        pkill -x -HUP panel_pidp1
}

do_stop() {
	#kill any support programs that may be running
	pkill -x tapevis
	pkill -x pdp1_periphES
	pkill -x pdpsrv
	pkill -x panel_pidp1
	pkill -x vpanel_pdp1
	# its name is over the kernel's 15 characters, so match the command line
	pkill -f pdp1_usb_monitor

	sleep 0.5
	is_running
	if [ $? -eq 0 ]; then
	    echo "PiDP-1 is already stopped." >&2
	    status=1
	else
	    echo "Stopping PiDP-1"
	    #screen -S pidp1 -X quit
	    pkill -x pdp1
	    status=$?
	fi

	sleep 0.5
        # pdp1 may be running outside of screen
	pkill -x pdp1

	# pdp1 writes coremem as it exits, and refuses to start while another one runs, so wait
	# for it to be gone, at most 10 seconds. Its screen session ends just after it, and start
	# takes a session still there for a running PiDP-1, so wait for that too. is_running
	# returns the session count, so it succeeds when none is left.
	for i in $(seq 100); do
		if ! pdp1_running && is_running; then
			break
		fi
		sleep 0.1
	done
	if pdp1_running; then
		echo "pdp1 has not exited after 10 seconds." >&2
		status=1
	fi

	# t30dpy ends by itself when pdp1's display connection closes. Its SIGTERM handler can hang
	# it for good, so it is signaled only if it is still there after 3 seconds, and killed if
	# that does not end it.
	for i in $(seq 30); do
		pgrep -x 't30dpy|t30dpy3' > /dev/null || break
		sleep 0.1
	done
	if pgrep -x 't30dpy|t30dpy3' > /dev/null; then
		pkill -x 't30dpy|t30dpy3'
		for i in $(seq 20); do
			pgrep -x 't30dpy|t30dpy3' > /dev/null || break
			sleep 0.1
		done
		pkill -KILL -x 't30dpy|t30dpy3'
	fi

	return $status
}

do_set() {
	if [ -z "$2" ]; then
		echo "Error: No interface specified. Use 'gui', 'web', or 'apps'." >&2
		return 1
	fi
	
	case "$2" in
		gui|web|apps)
			if write_setting interface "$2"; then
				echo "Interface set to '$2', used at the next start"
				exit 0
			else
				echo "Error: Failed to update $settings" >&2
				return 1
			fi
			;;
		*)
			echo "Error: Invalid interface '$2'. Use 'gui', 'web', or 'apps'." >&2
			return 1
			;;
	esac
}

do_panel() {
	if [ -z "$2" ]; then
		echo "Error: No panel option specified. Use 'pidp' or 'virtual'." >&2
		return 1
	fi
	
	case "$2" in
		pidp|virtual)
			if write_setting frontpanel "$2"; then
				echo "Panel set to '$2', used at the next start"
				exit 0
			else
				echo "Error: Failed to update $settings" >&2
				return 1
			fi
			;;
		*)
			echo "Error: Invalid panel option '$2'. Use 'pidp' or 'virtual'." >&2
			return 1
			;;
	esac
}

do_usbtape() {
	if [ -z "$2" ]; then
		echo "Error: No usbtape option specified. Use 'y' or 'n'." >&2
		return 1
	fi
	
	case "$2" in
		y|n)
			if write_setting usbtape "$2"; then
				echo "usb_paper_tape set to '$2', used at the next start"
				exit 0
			else
				echo "Error: Failed to update $settings" >&2
				return 1
			fi
			;;
		*)
			echo "Error: Invalid usbtape option '$2'. Use 'y' or 'n'." >&2
			return 1
			;;
	esac
}

do_t30dpy() {
	if [ -z "$2" ]; then
		echo "Error: No t30dpy option specified. Use 'y' or 'n'." >&2
		return 1
	fi

	case "$2" in
		y|n)
			if write_setting t30dpy "$2"; then
				echo "t30dpy set to '$2', used at the next start"
				exit 0
			else
				echo "Error: Failed to update $settings" >&2
				return 1
			fi
			;;
		*)
			echo "Error: Invalid t30dpy option '$2'. Use 'y' or 'n'." >&2
			return 1
			;;
	esac
}

do_soroban() {
	if [ -z "$2" ]; then
		echo "Error: No soroban option specified. Use 'y' or 'n'." >&2
		return 1
	fi

	case "$2" in
		y|n)
			if write_setting soroban "$2"; then
				echo "soroban set to '$2', used at the next start"
				exit 0
			else
				echo "Error: Failed to update $settings" >&2
				return 1
			fi
			;;
		*)
			echo "Error: Invalid soroban option '$2'. Use 'y' or 'n'." >&2
			return 1
			;;
	esac
}


case "$1" in
  start)
	refuse_if_service
	do_start $1 $2
	;;

  stop)
	refuse_if_service
	do_stop
	;;

  restart)
	refuse_if_service
	do_stop
	do_start $1 $2
	;;

  reload)
	do_reload
	;;

  reloadt30)
	do_t30reload
	;;

  reloadpanel)
	do_panelreload
	;;

  set)
	do_set $1 $2
	;;
  panel)
	do_panel $1 $2
	;;
  usbtape)
	do_usbtape $1 $2
	;;
  t30dpy)
	do_t30dpy $1 $2
	;;
  soroban)
	do_soroban $1 $2
	;;

  status)
	screen -ls pidp1 | grep -E '[0-9]+\.pidp1'
	;;

  stat)
	do_stat
	;;
  ?)
	echo "Usage: pdp1control {start|stop|reload|restart|set|panel|usbtape|t30dpy|soroban|status|stat}" || true
	echo "       pdp1control {reloadt30|reloadpanel}" || true
	exit 1
	;;
  *)
	do_stat
	# A pdp1.service machine is not this script's to stop: do_stat has said how.
	service_running && exit 0
	if [ $status = 0 ]; then
		read -p "(S)tart, Start with boot (number), or (C)ancel? " respx
		#read -p "(S)tart or (C)ancel? " respx
		case $respx in
			[Ss]* )
				do_start
				;;
			[0-9]* )
				#boot_number=$respx
				# convert to decimal
				#boot_number=$((8#$ooot_number))
				set -- "start" "$respx"
				echo reassigned s2 to .$2. and s1 is .$1.
				do_start $1 $2
				;;
			[Cc]* )
				exit 1
				;;
			* )
				echo "Please answer with S or C.";;
				#echo "Please answer with S, a boot number, or C.";;
		esac
	else
		read -p "(S)top or (C)ancel? " respx
		case $respx in
			[Ss]* )
				do_stop
				;;
			[Cc]* )
				exit 1
				;;
			* )
				echo "Please answer with S or C.";;
		esac
	fi
esac
exit 0

