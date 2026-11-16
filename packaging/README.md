# Packaging the PiDP-1 software

The same shape as the PiDP-10 packaging (obsolescence.dev's pidp10): a spec
here, `packaging/build-rpm.sh` staging the sources from git, `make rpm` /
`make rpmlint` at the top level, and `.copr/Makefile` producing the SRPM for
COPR "build from git".

    make rpm                      # ./dist-rpm/pidp1-mods-*.rpm + src.rpm
    make rpm WORKTREE=yes         # package the tree as it stands (testing)
    make rpmlint                  # build, then rpmlint -c rpmlint.toml
    packaging/build-rpm.sh --srpm-only dist-rpm    # COPR's flow

## Layout

The single source of truth for where things live is the pair
`src/common/pidp1_paths.h` (compiled programs) and `bin/pidp1-env.sh`
(scripts); the spec installs to exactly what they say.

| Home | Contents |
|---|---|
| `/usr/share/pidp1-mods` | read-only tree mirror: `bin/` scripts, `tapes/`, `bootcfg/`, `Microtapes/`, `Drums/`, `Docs/`, `Am1Includes/`, `FunStuff/`, `web_pdp1/` |
| `/var/lib/pidp1-mods` | what the machine writes: `pdp23drum`, `coremem`, `punch.out`, and group-writable `tapes/` and `bootcfg/` seeded on first install from the read-only masters |
| `/etc/pidp1-mods` | `pidp1.config`, `t30dpy.config`, `microtapes.txt`, `usb_paper_tape_ports.cfg` - `%config(noreplace)` |
| `/usr/lib/pidp1-mods/IOTs` | the `.so` plugins the emulator `dlopen()`s (plain `/usr/lib` on every arch: absolute-path plugins are not the dynamic linker's business) |
| `/usr/libexec/pidp1-mods` | `pdp1`, panel drivers, peripheral simulators, `pdpsrv` - what the scripts start |
| `/usr/bin` | the user commands and the `man` front doors `pdp1` and `pdp1control` |

The group `pidp1-mods` (created by the sysusers fragment) owns the writable
state: the state directory, `/etc/pidp1-mods` (pdp1central saves
`pidp1.config`), and the `Microtapes/` and `Drums/` data directories the IOTs
write images into. Add the operators who run the panel:

    usermod -aG pidp1-mods <name>

## Notes and deliberate deviations

* There is no systemd service: the simulator is interactive (the front door
  is `pdp1control`), unlike pidp10's unit-managed engine. The autostart path
  is the `pdp1startup.desktop` template in `~/.config/autostart`.
* No subpackages yet. A `-panel` split (newpanel, pidp1_test, scanpf) is
  worth it when a machine with real PiDP-1 hardware and a headless box stop
  wanting the same dependency set.
* The hardware panel driver is shipped without setuid; a cabinet runs
  `src/panel_pidp1/setpriv.sh` (or waits for the libgpiod + udev route).
* `web_pdp1/vendor/` (gorilla/websocket, BSD-2) is committed so `%build`
  needs no network; that is the package's one vendored blob.
* rpmlint exceptions, each with its reason, are in `rpmlint.toml` - not in
  someone's scrollback.
