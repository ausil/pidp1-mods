# Packaging the PiDP-1 software

The same shape as the PiDP-10 packaging (obsolescence.dev's pidp10): a spec
here, `packaging/build-rpm.sh` staging the sources from git, `make rpm` /
`make rpmlint` at the top level, and `.copr/Makefile` producing the SRPM for
COPR "build from git".

    make rpm                      # ./dist-rpm/pidp1-mods-*.rpm + src.rpm
    make rpm WORKTREE=yes         # package the tree as it stands (testing)
    make srpm                     # source RPM only (COPR's flow), no compile
    make rpmlint                  # build, then rpmlint -c rpmlint.toml
    packaging/build-rpm.sh --srpm-only dist-rpm    # COPR's flow, by hand

## Layout

The single source of truth for where things live is the pair
`src/common/pidp1_paths.h` (compiled programs) and `bin/pidp1-env.sh`
(scripts); the spec installs to exactly what they say.

| Home | Contents |
|---|---|
| `/usr/share/pidp1-mods` | read-only tree mirror: `bin/` scripts, `Microtapes/`, `Drums/`, `Docs/`, `Am1Includes/`, `FunStuff/`, `web_pdp1/` |
| `/var/lib/pidp1-mods` | what the machine reads and writes: `pdp23drum`, `coremem`, `punch.out`, and the shipped `tapes/` library and `bootcfg/` — package-owned `%config(noreplace)` content, group-owned by `pidp1-mods` so the operators can edit it: site edits survive upgrades (the shipped update lands as `.rpmnew`), files you add yourself are never touched |
| `/etc/pidp1-mods` | `pidp1.config`, `t30dpy.config`, `microtapes.txt`, `usb_paper_tape_ports.cfg` - `%config(noreplace)` |
| `/usr/lib/pidp1-mods/IOTs` | the `.so` plugins the emulator `dlopen()`s (plain `/usr/lib` on every arch: absolute-path plugins are not the dynamic linker's business) |
| `/usr/libexec/pidp1-mods` | `pdp1`, panel drivers, peripheral simulators, `pdpsrv` - what the scripts start |
| `/usr/bin` | the user commands and the `man` front doors `pdp1` and `pdp1control` |

The group `pidp1-mods` (created by the sysusers fragment) owns the writable
state: the state directory, `/etc/pidp1-mods` (pdp1central saves
`pidp1.config`), and the `Microtapes/` and `Drums/` data directories the IOTs
write images into. Add the operators who run the panel:

    usermod -aG pidp1-mods <name>

## Starting the machine at boot

Three units boot the simulator without a login, all of them
**preset-disabled** — installing the package never starts anything on its
own; the operator enables them once:

    sudo systemctl enable --now pdp1 pdp1-panel pdp1-bootcfg

| Unit | Runs |
|---|---|
| `pdp1.service` | the emulator (`/usr/libexec/pidp1-mods/pdp1`), restarted if it fails |
| `pdp1-panel.service` | the cabinet's physical panel driver — enable on a real PiDP-1 only; without the hardware it exits and `Restart=` would cycle it |
| `pdp1-bootcfg.service` | oneshot feeding `bootcfg/<number>.cfg` to the command port, the way `pdp1control start` does |

All three run as the `pidp1-mods` user (added to the sysusers fragment next
to its group); the group already owns the state directory, `/etc/pidp1-mods`
and the panel's GPIO nodes, so the units need no privileges. The boot
images need no fetching either: the package installs `tapes/` and `bootcfg/`
straight into `/var/lib/pidp1-mods`, and a new `.rim` dropped into `tapes/`
is reachable from a `bootcfg/<n>.cfg` via `PDP1_DIR/tapes/`.

The boot number names the `bootcfg/<number>.cfg` to load. `pdp1-bootcfg`
reads it from the panel's sense switches (`scanpf`, all-down → `0`) unless
`PDP1_BOOT_NUMBER` says otherwise — set it persistently with
`systemctl edit pdp1-bootcfg` and `Environment=PDP1_BOOT_NUMBER=2`. No
matching config, or no `0.cfg`, and the machine boots idle, like `pdp1control`.
`pdp1` uses SDL2 for audio only; a cabinet with no sound card can silence
its init with a drop-in `Environment=SDL_AUDIODRIVER=dummy`.

Desktop use is unchanged: `pdp1control` starts the same programs in a
`screen` session, and `pdp1startup.desktop` remains the autostart path.
Don't run both — the units and a desktop session compete for the panel and
the ports.

## Remote access

Every server in the package binds to all interfaces — a `pdpsrv` or a
`t30dpy` on another machine reaching the emulator is the design — so remote
use needs no code, only firewall openings, and a machine with no firewall
running exposes all of it to the LAN. Loopback always works and needs
nothing; the cabinet and the `bin/` scripts are all `127.0.0.1`.

The remote operator installs just the clients, SDL2 and nothing else from us:

    sudo dnf install pidp1-mods-clients
    t30dpy <cabinet>          # screen 0; -p 3401..3 for the other three
    tapevis -h <cabinet>      # paper-tape reader and punch on the network
    ad1 ...                   # the debugger, see the documentation

| Port | Server | What it is |
|---|---|---|
| 8080/tcp | `pdpsrv` | the web front end |
| 1040/tcp | `pdp1` | command port: load, run/cont/halt — treat like SSH |
| 1041/tcp | `pdp1` | typewriter telnet (Soroban); plain text |
| 1042/1043/tcp | `pdp1` | paper-tape reader / punch |
| 1050/tcp | `pdp1_periph[ES]`, `tapevis`, `pdpsrv` | peripheral command port |
| 3400-3403/tcp | `pdp1` | Type 30 display screens (remote `t30dpy <host>` clients) |
| 1044/tcp | `pdp1` | ad1 debugger — loopback only, needs nothing |
| 1045/tcp | `pdp1` | remote ad1 — `ad1remoteport`, off by default |

Two opt-in firewalld services ship with the package; nothing opens at
install:

    sudo firewall-cmd --permanent --add-service=pidp1-mods        # everything above but 1045
    sudo firewall-cmd --permanent --add-service=pidp1-mods-debug  # 1045, with ad1remoteport on
    sudo firewall-cmd --reload

## Notes and deliberate deviations

* The boot-time units exist but are preset-disabled — the desktop front door
  stays `pdp1control`, so booting into the simulator is the operator's
  call, not the package manager's (see *Starting the machine at boot*).
* One subpackage: `pidp1-mods-clients` — `t30dpy`, `tapevis` and `ad1`,
  the programs that talk to a pdp1 over the network instead of being the
  machine. It exists for the box that only watches or debugs a remote
  pdp1: SDL2 and nothing else from us, no emulator, no panel code. The
  main package `Recommends:` it, so a cabinet install is unchanged
  (`pdp1control start` still starts `t30dpy` and `tapevis` beside the
  machine). The split is by workflow, not by tool: per-tool packages
  would each cost a debuginfo and a version pin to say "I do not want
  SDL2". A `-panel` split (newpanel, pidp1_test, scanpf) is worth it when
  a machine with real PiDP-1 hardware and a headless box stop wanting the
  same dependency set.
* The hardware panel driver is shipped without setuid: it drives the panel
  through libgpiod, and the packaged `60-pidp1-mods.rules`
  (`/usr/lib/udev/rules.d`) hands the panel's controller -
  `pinctrl-bcm2835` on a Pi 4 or earlier, `pinctrl-rp1` on a Pi 5 - to the
  pidp1-mods group; cabinet users need only `usermod -aG pidp1-mods`. The
  gpiomem nodes are group-accessible too, for the register backend that
  still owns anything libgpiod cannot express. `setpriv.sh` remains for the
  `/dev/mem` fallback on kernels with neither path.
* `web_pdp1/vendor/` (gorilla/websocket, BSD-2) is committed so `%build`
  needs no network; that is the package's one vendored blob.
* rpmlint exceptions, each with its reason, are in `rpmlint.toml` - not in
  someone's scrollback.
