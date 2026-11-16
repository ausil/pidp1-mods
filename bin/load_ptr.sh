#!/bin/bash
#
# Mount a paper tape on the reader: choose the file in a dialog and hand the emulator the
# absolute path on the front end's command port.
. "${PIDP1_ENV:-$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/pidp1-env.sh}"

# Start the chooser in the tape library
ABS_FILE=$(zenity --file-selection --title="Choose a file" --filename="${PIDP1_TAPES}/")

# zenity 3 exits 1 on a cancel; zenity 4 exits 0 and prints nothing, and a bare "r" would
# unmount the reader.
if [ $? -ne 0 ] || [ -z "$ABS_FILE" ]; then
    echo "Cancelled."
    exit 1
fi

# Send the absolute path, not a path relative to the tape library: whichever backend is listening
# on port 1050 (the C pdp1_periphES daemon, or pdpsrv.go under the "web" interface) opens
# this path as-is, relative to its OWN current working directory, which is not guaranteed
# to be the tape library (e.g. pdp1control.sh cd's into the web directory before launching
# pdpsrv). A relative path here silently fails to load on the far end with no visible error,
# since pdp1control.sh redirects that backend's stderr to /dev/null. tui_load_ptr.sh already
# uses the absolute path for the same reason.
echo "Sending path: $ABS_FILE"

echo "r $ABS_FILE" | ncat -w 1 localhost 1050
