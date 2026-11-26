/*
 * libgpiod backend: the panel's GPIO operations through the kernel GPIO
 * character device. See gpiolib_gpiod.h for when this path is used and why.
 *
 * HARD SAFETY RULE - auto-detection must say no.
 *   The panel is wired to legacy BCM numbers which are only "the same thing"
 *   on a Raspberry Pi header controller. /dev/gpiochipN exists on plenty of
 *   machines that are not PiDP-1 cabinets - including a real Pi 5, where
 *   Fedora's kernel registers several 32-line brcmstb-gpio blocks (and
 *   laptops have a dozen PMIC gpiochips) ahead of the header controller.
 *   Claiming line 22 of one of those because its name merely contains
 *   "brcm" is a bug with smoke coming out of the machine (an earlier cut of
 *   this file matched substrings and drove a cabinet's panel into a dead
 *   controller), so a chip is only auto-selected when its name or label
 *   *equals* one of the three header controller drivers: pinctrl-bcm2835,
 *   pinctrl-bcm2711, pinctrl-rp1. Everything else needs PIDP1_GPIO_CHIP
 *   *plus* PIDP1_PANEL_FORCE, which is the operator overriding the check on
 *   purpose - two settings, so one typo is not enough to start driving a
 *   power rail.
 *
 * One line request per GPIO, cached with the direction and bias it was
 * requested with. A direction or pull change is applied in place with
 * gpiod_line_request_reconfigure_lines(): the kernel tracks line ownership
 * per gpio device, so requesting a line this process still holds fails
 * EBUSY - release-then-request cannot work - and reconfigure is also a
 * single ioctl with no window where a column line sits unclaimed and
 * floating between frames. The panel touches a couple of dozen lines at a
 * scan cadence of tens of Hz, so per-line requests are comfortably cheap
 * here - unlike the PiDP-10 panel, which drives a whole matrix row per
 * frame and batches the row into as few LINE_SET_VALUES ioctls as the API
 * allows.
 *
 * Bias follows the register backend's semantics: the pull hardware is
 * independent of direction and is only ever touched by gpio_set_pull().
 * Line settings therefore leave bias at AS_IS (the kernel does not touch
 * the pull hardware at all) except when gpio_set_pull asked for a pull we
 * have not already written; that keeps the firmware's power-on pulls on
 * lines the panel never configures, which a blanket bias DISABLED on every
 * request silently destroyed (every button read released).
 */

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gpiod.h>

#include "gpiolib.h"
#include "gpiolib_gpiod.h"

#ifdef HAVE_GPIOD

#define MAX_CHIP_INDEX 32
#define GPIOD_CONSUMER "pidp1"

// One requested line and what it was requested as; the cache lets a 100 Hz
// scan loop skip the ioctl round-trips when nothing about the line changed.
typedef struct GPIOD_LINE_
{
    struct gpiod_line_request *reqP;
    GPIO_DIR_T dir;
    GPIO_PULL_T pull;
    int value;            // last driven level; the reconfigure that puts the
                          // line back in output mode applies it
    int have_dir;
    int have_pull;        // the caller has called gpio_set_pull on this line
    int hwPull;           // (int)pull + 1 of the bias last written to the
                          // kernel, 0 = never written (bias left AS_IS)
} GPIOD_LINE_T;

static struct gpiod_chip *chipP;
static struct gpiod_request_config *reqconfP;    // consumer name, built once
static size_t chipLines;
static int active;
static GPIOD_LINE_T lines[MAX_GPIO_PINS];
static void (*verbose_callback)(const char *);
static int warned_alt;
static int warned_io;
static int probeOpenErrno;      // first non-ENOENT open failure of the scan

static void
logMsg(const char *fmt, ...)
{
va_list ap;
char buf[256];

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    if( verbose_callback )
    {
        (*verbose_callback)(buf);
    }
    else if( buf[0] == '!' )   // "!" prefix: a real problem, say it once anyway
    {
        fprintf(stderr, "gpiolib(gpiod): %s\n", buf + 1);
    }
}

// The 40-pin header controller, by the exact name the mainline driver
// registers (and the Raspberry Pi kernel uses the same): Pi 0-3,
// Pi 4/400/CM4, and Pi 5/CM5 where the RP1 sits behind PCIe. Comparison is
// deliberately *not* substring matching, and there is no "first chip that
// opens" fallback - see the safety rule at the top of the file. Returns the
// rank in the want list (earlier wins should a machine ever expose two), or
// -1 for "not the header".
static int
header_controller(const char *name, const char *label)
{
static const char *const want[] = {
    "pinctrl-bcm2835", "pinctrl-bcm2711", "pinctrl-rp1", NULL
};
const char *const *p;
int rank;

    for( p = want, rank = 0; *p; p++, rank++ )
    {
        if( (name && !strcmp(name, *p)) || (label && !strcmp(label, *p)) )
        {
            return(rank);
        }
    }

    return(-1);
}

// Exact name-or-label comparison for the PIDP1_GPIO_CHIP override.
static int
name_matches(const char *name, const char *label, const char *want)
{
    return( (name && !strcmp(name, want)) || (label && !strcmp(label, want)) );
}

// "1"/"y"/"yes"/"on"/"true", lower-case spellings only: this is a
// footgun-disarmament flag, not a place to be generous about typing.
static int
env_yes(const char *var)
{
const char *v = getenv(var);

    return( v && (!strcmp(v, "1") || !strcmp(v, "y") || !strcmp(v, "yes") ||
                 !strcmp(v, "on") || !strcmp(v, "true")) );
}

// Opens candidate path and claims it unless the caller's filters reject it:
// requirePi demands the header controller (auto-select), wantName demands an
// exact name/label match (PIDP1_GPIO_CHIP given as a chip name), and the
// line-count floor guards auto-select (the panel's highest BCM number plus
// one). Takes ownership of a claimed chip.
static int
claimChip(const char *path, const char *wantName, int requirePi, size_t lineFloor)
{
struct gpiod_chip *c;
struct gpiod_chip_info *ci;
const char *name, *label;
size_t nlines;

    c = gpiod_chip_open(path);
    if( !c )
    {
        if( (errno != ENOENT) && !probeOpenErrno )
        {
            probeOpenErrno = errno;
        }

        return(0);
    }

    ci = gpiod_chip_get_info(c);
    if( !ci )
    {
        gpiod_chip_close(c);
        return(0);
    }

    name = gpiod_chip_info_get_name(ci);
    label = gpiod_chip_info_get_label(ci);
    nlines = gpiod_chip_info_get_num_lines(ci);

    if( wantName && !name_matches(name, label, wantName) )
    {
        gpiod_chip_info_free(ci);
        gpiod_chip_close(c);
        return(0);
    }

    if( requirePi && (header_controller(name, label) < 0) )
    {
        logMsg("skipping %s (%s/%s): not the 40-pin header controller",
            path, name ? name : "?", label ? label : "?");
        gpiod_chip_info_free(ci);
        gpiod_chip_close(c);
        return(0);
    }

    if( nlines < lineFloor )
    {
        logMsg("skipping %s: %zu lines, panel needs %zu", path, nlines, lineFloor);
        gpiod_chip_info_free(ci);
        gpiod_chip_close(c);
        return(0);
    }

    logMsg("using %s (%s/%s, %zu lines) via libgpiod",
        path, name ? name : "?", label ? label : "?", nlines);

    gpiod_chip_info_free(ci);
    chipP = c;
    chipLines = nlines;
    active = 1;

    if( !reqconfP )
    {
        reqconfP = gpiod_request_config_new();
        if( reqconfP )
        {
            gpiod_request_config_set_consumer(reqconfP, GPIOD_CONSUMER);
        }
    }

    return(1);
}

// See gpiolib_gpiod.h.
int
gpiod_backend_probe(void)
{
char path[64];
const char *want;
unsigned i;

    if( active )
    {
        return(1);
    }

    if( env_yes("PIDP1_NO_GPIOD") )
    {
        logMsg("PIDP1_NO_GPIOD is set; register backend only");
        return(0);
    }

    want = getenv("PIDP1_GPIO_CHIP");
    if( want && *want )
    {
        if( want[0] == '/' )
        {
            // A full path is taken as given; the header-controller check
            // still gates it unless PIDP1_PANEL_FORCE says otherwise.
            if( claimChip(want, NULL, !env_yes("PIDP1_PANEL_FORCE"), 0) )
            {
                return(1);
            }
        }
        else
        {
            // snprintf: the name comes from the environment, and a long one
            // must not run off the end of path. A truncated path names no
            // device, so it simply falls through to the name match below.
            snprintf(path, sizeof(path), "/dev/%s", want);
            if( claimChip(path, NULL, !env_yes("PIDP1_PANEL_FORCE"), 0) )
            {
                return(1);
            }

            // Not a device file after all: accept it as a chip name/label
            // ("pinctrl-rp1") on whichever gpiochipN carries it.
            for( i = 0; i < MAX_CHIP_INDEX; i++ )
            {
                snprintf(path, sizeof(path), "/dev/gpiochip%u", i);
                if( claimChip(path, want, 0, 0) )
                {
                    return(1);
                }
            }
        }

        fprintf(stderr, "gpiolib(gpiod): PIDP1_GPIO_CHIP=%s was not usable\n", want);
        return(0);
    }

    // No iteration API in libgpiod v2; scan the conventional paths. A
    // machine without the header controller ends with active == 0 and the
    // caller falls back to (or keeps) the register path - which then says
    // "no panel" honestly, exactly as before.
    for( i = 0; i < MAX_CHIP_INDEX; i++ )
    {
        snprintf(path, sizeof(path), "/dev/gpiochip%u", i);
        if( claimChip(path, NULL, 1, 28) )   // highest panel BCM number + 1
        {
            return(1);
        }
    }

    logMsg("no header controller (pinctrl-bcm2835/-bcm2711/-rp1) among "
        "/dev/gpiochip0..%d; compare gpiodetect(1) - on a Pi 5 the RP1 "
        "drivers (rp1_pci, pinctrl-rp1) are modules", MAX_CHIP_INDEX - 1);

    if( probeOpenErrno == EACCES )
    {
        logMsg("!a gpiochip could not be opened; check group membership "
            "(ls -l /dev/gpiochip*; id) and SELinux (ls -Z, "
            "ausearch -m avc -ts recent)");
    }

    return(0);
}

// See gpiolib_gpiod.h.
int
gpiod_backend_active(void)
{
    return(active);
}

// See gpiolib_gpiod.h.
unsigned
gpiod_backend_num_gpios(void)
{
    if( !active )
    {
        return(0);
    }

    return( (chipLines < MAX_GPIO_PINS) ? (unsigned)chipLines : MAX_GPIO_PINS );
}

// See gpiolib_gpiod.h.
void
gpiod_backend_set_verbose(void (*callback)(const char *))
{
    verbose_callback = callback;
}

static int
usable(unsigned gpio)
{
    return( active && (gpio < chipLines) && (gpio < MAX_GPIO_PINS) );
}

// Builds a single-line config in the requested state: direction, and - for
// output - the cached drive level, so a flip back to output comes up
// glitch-free with the value the lamp code asked for while the line was an
// input. setBias asks for a definite pull; otherwise bias stays AS_IS and
// the kernel leaves the pull hardware alone (see the file header). The
// offset is the chip line offset (the legacy BCM number), not a
// within-request index: libgpiod keys requested lines by their chip-side
// offset, and an index yields EINVAL for every pin but gpio 0.
static struct gpiod_line_config *
makeLineConfig(unsigned gpio, GPIO_DIR_T dir, GPIO_PULL_T pull, int value,
    int setBias)
{
struct gpiod_line_settings *ls;
struct gpiod_line_config *lc;
unsigned offset = gpio;

    ls = gpiod_line_settings_new();
    lc = gpiod_line_config_new();

    if( ls && lc )
    {
        gpiod_line_settings_set_direction(ls,
            (dir == DIR_OUTPUT) ? GPIOD_LINE_DIRECTION_OUTPUT
                                : GPIOD_LINE_DIRECTION_INPUT);

        if( dir == DIR_OUTPUT )
        {
            gpiod_line_settings_set_output_value(ls,
                value ? GPIOD_LINE_VALUE_ACTIVE : GPIOD_LINE_VALUE_INACTIVE);
        }

        if( setBias )
        {
            gpiod_line_settings_set_bias(ls,
                (pull == PULL_UP) ? GPIOD_LINE_BIAS_PULL_UP :
                (pull == PULL_DOWN) ? GPIOD_LINE_BIAS_PULL_DOWN
                                    : GPIOD_LINE_BIAS_DISABLED);
        }

        if( gpiod_line_config_add_line_settings(lc, &offset, 1, ls) == 0 )
        {
            gpiod_line_settings_free(ls);
            return(lc);         // caller frees
        }
    }

    if( ls )
    {
        gpiod_line_settings_free(ls);
    }

    if( lc )
    {
        gpiod_line_config_free(lc);
    }

    return(NULL);
}

// (Re)requests 'gpio' as dir/pull unless it is already held that way. A held
// line is reconfigured in place; the cache is only updated on success, so a
// refused change is retried on the next pass instead of being believed.
// Returns 0 (line left in whatever state the kernel has) on failure.
static int
ensureLine(unsigned gpio, GPIO_DIR_T dir, GPIO_PULL_T pull)
{
GPIOD_LINE_T *lineP = &lines[gpio];
struct gpiod_line_config *lc;
int setBias;
int rc;

    // The bias test belongs here too: a pull committed by set_pull but not
    // yet written (hwPull still says never) must re-trigger the reconfigure
    // on the next call rather than be believed.
    if( lineP->reqP && (lineP->dir == dir) && (lineP->pull == pull) &&
        ( !lineP->have_pull || (lineP->hwPull == ((int)pull + 1)) ) )
    {
        return(1);
    }

    setBias = lineP->have_pull && (lineP->hwPull != ((int)pull + 1));

    lc = makeLineConfig(gpio, dir, pull, lineP->value, setBias);
    if( !lc )
    {
        if( !warned_io )
        {
            warned_io = 1;
            logMsg("!line %u config failed (%s); the panel is deaf from here on",
                gpio, strerror(errno));
        }

        return(0);
    }

    if( lineP->reqP )
    {
        rc = gpiod_line_request_reconfigure_lines(lineP->reqP, lc);
    }
    else
    {
        lineP->reqP = gpiod_chip_request_lines(chipP, reqconfP, lc);
        rc = lineP->reqP ? 0 : -1;
    }

    gpiod_line_config_free(lc);

    if( rc )
    {
        if( !warned_io )
        {
            warned_io = 1;
            logMsg("!line %u %s failed (%s); the panel is deaf from here on",
                gpio, lineP->reqP ? "reconfigure" : "request", strerror(errno));
        }

        return(0);
    }

    lineP->dir = dir;
    lineP->pull = pull;
    lineP->have_dir = 1;

    if( lineP->have_pull )
    {
        lineP->hwPull = (int)pull + 1;
    }

    return(1);
}

// See gpiolib_gpiod.h.
int
gpiod_backend_num_is_valid(unsigned gpio)
{
    return(usable(gpio));
}

// See gpiolib_gpiod.h.
int
gpiod_backend_get_dir(unsigned gpio)
{
    if( !usable(gpio) || !lines[gpio].have_dir )
    {
        return(DIR_MAX);
    }

    return((int)lines[gpio].dir);
}

// See gpiolib_gpiod.h.
void
gpiod_backend_set_dir(unsigned gpio, GPIO_DIR_T dir)
{
    if( usable(gpio) )
    {
        ensureLine(gpio, dir,
            lines[gpio].have_pull ? lines[gpio].pull : PULL_NONE);
    }
}

// See gpiolib_gpiod.h.
// Only GPIO_FSEL_INPUT/GPIO_FSEL_OUTPUT have a libgpiod equivalent; the
// alternate functions are pin multiplexing, which the character device does
// not expose. For those the line is released entirely so the device tree's
// default function (whatever the overlay configures) can take the pad back;
// saying so once on stderr is the honest part.
void
gpiod_backend_set_fsel(unsigned gpio, GPIO_FSEL_T fsel)
{
    if( !usable(gpio) )
    {
        return;
    }

    if( fsel == GPIO_FSEL_OUTPUT )
    {
        ensureLine(gpio, DIR_OUTPUT,
            lines[gpio].have_pull ? lines[gpio].pull : PULL_NONE);
        return;
    }

    if( fsel == GPIO_FSEL_INPUT )
    {
        ensureLine(gpio, DIR_INPUT,
            lines[gpio].have_pull ? lines[gpio].pull : PULL_NONE);
        return;
    }

    if( lines[gpio].reqP )
    {
        gpiod_line_request_release(lines[gpio].reqP);
        lines[gpio].reqP = NULL;
        lines[gpio].have_dir = 0;
        lines[gpio].hwPull = 0;     // the alt function may have its own pull
    }

    if( !warned_alt )
    {
        warned_alt = 1;
        logMsg("!fsel %d requested without the register backend; the line "
            "was released so the device tree function can claim it",
            (int)fsel);
    }
}

// See gpiolib_gpiod.h.
// GPIO_DRIVE_T here is the driven level (DRIVE_LOW/DRIVE_HIGH), matching how
// newpanel drives the lamp matrix through gpio_set_drive().
void
gpiod_backend_set_drive(unsigned gpio, GPIO_DRIVE_T drv)
{
    if( !usable(gpio) )
    {
        return;
    }

    lines[gpio].value = (drv == DRIVE_HIGH);

    // Only touch hardware while the line actually drives the pin; while it
    // is an input this just updates the value the next output reconfiguration
    // applies - the same glitch-free pattern as the register backend, whose
    // data register is independent of the direction too. Never force the
    // line to output from here: the lamp code drives while the column side
    // of the matrix is deliberately blanked to input.
    if( lines[gpio].reqP && (lines[gpio].dir == DIR_OUTPUT) )
    {
        if( gpiod_line_request_set_value(lines[gpio].reqP, gpio,
                (drv == DRIVE_HIGH) ? GPIOD_LINE_VALUE_ACTIVE
                                    : GPIOD_LINE_VALUE_INACTIVE) )
        {
            if( !warned_io )
            {
                warned_io = 1;
                logMsg("!line %u set failed (%s)", gpio, strerror(errno));
            }
        }
    }
}

// See gpiolib_gpiod.h.
void
gpiod_backend_set_multi_drive(const int *gpios, const GPIO_DRIVE_T *drvs, int count)
{
int i;

    for( i = 0; i < count; i++ )
    {
        gpiod_backend_set_drive((unsigned)gpios[i], drvs[i]);
    }
}

// gpio_set()/gpio_clear() are "drive this level, as an output" in the
// register backend (gpiolib.c writes the level, then the direction), unlike
// gpio_set_drive(), which only latches the level. Same order here: the
// cached value is what the output reconfiguration comes up driving, so the
// pin never shows the old level, and a line already held as output gets the
// one set_value ioctl and no reconfigure.
static void
driveAsOutput(unsigned gpio, GPIO_DRIVE_T drv)
{
    if( !usable(gpio) )
    {
        return;
    }

    gpiod_backend_set_drive(gpio, drv);
    ensureLine(gpio, DIR_OUTPUT,
        lines[gpio].have_pull ? lines[gpio].pull : PULL_NONE);
}

// See gpiolib_gpiod.h.
void
gpiod_backend_set(unsigned gpio)
{
    driveAsOutput(gpio, DRIVE_HIGH);
}

// See gpiolib_gpiod.h.
void
gpiod_backend_clear(unsigned gpio)
{
    driveAsOutput(gpio, DRIVE_LOW);
}

// See gpiolib_gpiod.h.
// A read never changes what the line is doing. The register backend samples
// the level register whatever the direction, and the v2 character device
// does the same: GET_VALUES works on a line requested as output. So only a
// line this process does not hold yet is requested, as an input, which
// is what reading an unconfigured pin means. A held output stays an output.
// (The pidp8i fixup forces input here, on the belief that sampling needs an
// input-side request; that would let a stray read during outRow() blank a
// lit column, and the scan loop's own inRow() makes it unnecessary anyway.)
int
gpiod_backend_get_level(unsigned gpio)
{
enum gpiod_line_value value;
GPIOD_LINE_T *lineP;

    if( !usable(gpio) )
    {
        return(0);
    }

    lineP = &lines[gpio];

    if( !lineP->reqP &&
        !ensureLine(gpio, DIR_INPUT,
            lineP->have_pull ? lineP->pull : PULL_NONE) )
    {
        return(0);
    }

    // v2 returns the level directly: 1/0, or -1 on error. The second
    // argument is the chip line offset even though the request holds one
    // line - see makeLineConfig().
    value = gpiod_line_request_get_value(lineP->reqP, gpio);
    if( value == GPIOD_LINE_VALUE_ERROR )
    {
        if( !warned_io )
        {
            warned_io = 1;
            logMsg("!line %u get failed (%s)", gpio, strerror(errno));
        }

        return(0);
    }

    return(value == GPIOD_LINE_VALUE_ACTIVE);
}

// See gpiolib_gpiod.h.
int
gpiod_backend_get_pull(unsigned gpio)
{
    if( !usable(gpio) || !lines[gpio].have_pull )
    {
        return(PULL_MAX);
    }

    return((int)lines[gpio].pull);
}

// See gpiolib_gpiod.h.
// The register backend's pull registers take effect regardless of the
// direction, so an applied pull is applied now; an unheld line picks it up
// at its next request through the same path.
void
gpiod_backend_set_pull(unsigned gpio, GPIO_PULL_T pull)
{
    if( !usable(gpio) )
    {
        return;
    }

    // Committed up front (not on success) so a refused request is retried
    // by the next operation on the line: hwPull still marks the bias as
    // unwritten, which keeps the early return in ensureLine from believing
    // the request happened.
    lines[gpio].pull = pull;
    lines[gpio].have_pull = 1;

    ensureLine(gpio, lines[gpio].have_dir ? lines[gpio].dir : DIR_INPUT, pull);
}

#endif /* HAVE_GPIOD */
