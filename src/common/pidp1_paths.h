/*
 * pidp1_paths.h -- where the installed programs find their files.
 *
 * The tree used to be a checkout that had to live in /opt/pidp1-mods, with that
 * path written out in about forty places. Installed as an RPM the pieces go to
 * their normal FHS homes instead, and this is the one place that says where:
 *
 *   PIDP1_DATADIR     /usr/share/pidp1-mods      read-only program data: the tape
 *                                                 library, Microtapes, Drums, the
 *                                                 Am1 include files, Docs, FunStuff,
 *                                                 the web assets.
 *   PIDP1_STATEDIR    /var/lib/pidp1-mods        what the running machine writes:
 *                                                 the Type 23 drum image, coremem,
 *                                                 and tapes/, the tape library the
 *                                                 panel's selector boots from.
 *   PIDP1_SYSCONFDIR  /etc/pidp1-mods            the site's configuration:
 *                                                 pidp1.config, t30dpy.config,
 *                                                 microtapes.txt, usb_paper_tape_ports.cfg
 *   PIDP1_IOTDIR      /usr/lib/pidp1-mods/IOTs   the dynamic IOT plugins the
 *                                                 emulator dlopen()s.
 *   PIDP1_LIBEXECDIR  /usr/libexec/pidp1-mods    the emulator, panel driver and
 *                                                 peripheral simulators, which are
 *                                                 started by the scripts rather
 *                                                 than typed by a user.
 *
 * Every path is a compile-time literal, so they can still initialize static
 * objects the way the string they replace did. A distribution that wants them
 * elsewhere passes -DPIDP1_STATEDIR='"/somewhere/else"' in CFLAGS; nothing has to
 * be edited. Keep the values in step with the spec file, which owns the same
 * directories.
 *
 * 15-Nov-2026 wje split out of the /opt/pidp1-mods hard-coding for the Fedora RPM.
 */
#ifndef PIDP1_PATHS_H
#define PIDP1_PATHS_H

#ifndef PIDP1_DATADIR
#define PIDP1_DATADIR       "/usr/share/pidp1-mods"
#endif

#ifndef PIDP1_STATEDIR
#define PIDP1_STATEDIR      "/var/lib/pidp1-mods"
#endif

#ifndef PIDP1_SYSCONFDIR
#define PIDP1_SYSCONFDIR    "/etc/pidp1-mods"
#endif

#ifndef PIDP1_IOTDIR
#define PIDP1_IOTDIR        "/usr/lib/pidp1-mods/IOTs"
#endif

#ifndef PIDP1_LIBEXECDIR
#define PIDP1_LIBEXECDIR    "/usr/libexec/pidp1-mods"
#endif

#ifndef PIDP1_BINDIR
#define PIDP1_BINDIR        "/usr/bin"
#endif

/* The pieces themselves, spelled the way the call sites used to spell them out. */

#define PIDP1_CONFIG        PIDP1_SYSCONFDIR "/pidp1.config"
#define PIDP1_T30DCONFIG    PIDP1_SYSCONFDIR "/t30dpy.config"
#define PIDP1_PORTCFG       PIDP1_SYSCONFDIR "/usb_paper_tape_ports.cfg"
#define PIDP1_MOUNTLIST     PIDP1_SYSCONFDIR "/microtapes.txt"

#define PIDP1_DRUMFILE      PIDP1_STATEDIR "/pdp23drum"
#define PIDP1_COREMEM       PIDP1_STATEDIR "/coremem"
#define PIDP1_TAPEDIR       PIDP1_STATEDIR "/tapes"

#define PIDP1_MICROTAPEDIR  PIDP1_DATADIR "/Microtapes"
#define PIDP1_DRUMDIR       PIDP1_DATADIR "/Drums"
#define PIDP1_AM1INCDIR     PIDP1_DATADIR "/Am1Includes"

#endif /* PIDP1_PATHS_H */
