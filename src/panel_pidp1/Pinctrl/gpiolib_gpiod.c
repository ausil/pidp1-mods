/*
 * libgpiod backend: the panel's GPIO operations through the kernel GPIO
 * character device. See gpiolib_gpiod.h for when this path is used and why.
 *
 * HARD SAFETY RULE - auto-detection must say no.
 *   The panel is wired to legacy BCM numbers which are only "the same thing"
 *   on a Raspberry Pi controller. /dev/gpiochipN exists on plenty of machines
 *   that are not PiDP-1 cabinets (a Qualcomm laptop has fourteen of them,
 *   most of them PMIC rails that drive real power hardware). Claiming line 22
 *   of some random PMIC gpiochip because it "looks free" would be a bug with
 *   smoke coming out of the machine, so a chip is only auto-selected when its
 *   name/label identifies a Broadcom controller (see pi_controller()).
 *   Everything else needs PIDP1_GPIO_CHIP *plus* PIDP1_PANEL_FORCE, which is
 *   the operator overriding the check on purpose - two settings, so one typo
 *   is not enough to start driving a power rail.
 *
 * One line request per GPIO, cached with the direction and bias it was
 * requested with; a reconfigure (direction or pull change) releases and
 * re-requests the single line. The panel touches a couple of dozen lines at
 * a scan cadence of tens of Hz, so per-line requests are comfortably cheap
 * here - unlike the PiDP-10 panel, which drives a whole matrix row per frame
 * and batches the row into as few LINE_SET_VALUES ioctls as the API allows.
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

// One requested line and what it was requested as; the cache lets a 100 Hz
// scan loop skips the ioctl round-trips when nothing about the line changed.
typedef struct GPIOD_LINE_
{
    struct gpiod_line_request *reqP;
    GPIO_DIR_T dir;
    GPIO_PULL_T pull;
    int value;            // last driven level, kept across re-requests
    int have_dir;
    int have_pull;
} GPIOD_LINE_T;

static struct gpiod_chip *chipP;
static size_t chipLines;
static int active;
static GPIOD_LINE_T lines[MAX_GPIO_PINS];
static void (*verbose_callback)(const char *);
static int warned_alt;
static int warned_io;

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

// Lower-case substring match over both name and label, because the kernel
// fills them differently per platform (and on non-Pi machines the label is
// an OF node path like "c42d000.spmi:pmic@0:gpio@8800", which must NOT
// match). Same hit list pidp10's pidp_panel_gpiod.c uses.
static int
pi_controller(const char *name, const char *label)
{
static const char *const hits[] = {
    "brcm", "bcm2835", "bcm2708", "bcm2709", "bcm2711", "bcm2712",
    "raspberry", "rp1", NULL
};
const char *const *p;

    for( p = hits; *p; p++ )
    {
        if( (name && strstr(name, *p)) || (label && strstr(label, *p)) )
        {
            return(1);
        }
    }

    return(0);
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

// Opens candidate path and claims it unless the name/label check (when
// requirePi) or the line-count floor (auto-select: the panel's highest BCM
// number plus one) rejects it. Takes ownership of a claimed chip.
static int
claimChip(const char *path, int requirePi, size_t lineFloor)
{
struct gpiod_chip *c;
struct gpiod_chip_info *ci;
const char *name, *label;
size_t nlines;

    c = gpiod_chip_open(path);
    if( !c )
    {
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

    if( requirePi && !pi_controller(name, label) )
    {
        logMsg("skipping %s (%s/%s): not a Broadcom GPIO controller",
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
            // A full path is taken as given; the Broadcom check still gates
            // it unless PIDP1_PANEL_FORCE says otherwise.
            if( claimChip(want, !env_yes("PIDP1_PANEL_FORCE"), 0) )
            {
                return(1);
            }
        }
        else
        {
            sprintf(path, "/dev/%s", want);
            if( claimChip(path, !env_yes("PIDP1_PANEL_FORCE"), 0) )
            {
                return(1);
            }
        }

        fprintf(stderr, "gpiolib(gpiod): PIDP1_GPIO_CHIP=%s was not usable\n", want);
        return(0);
    }

    // No iteration API in libgpiod v2; scan the conventional paths. A
    // machine without a Broadcom controller ends with active == 0 and the
    // caller falls back to (or keeps) the register path - which then says
    // "no panel" honestly, exactly as before.
    for( i = 0; i < MAX_CHIP_INDEX; i++ )
    {
        sprintf(path, "/dev/gpiochip%u", i);
        if( claimChip(path, 1, 28) )   // highest panel BCM number + 1
        {
            return(1);
        }
    }

    logMsg("no Broadcom GPIO controller among /dev/gpiochip0..%d", MAX_CHIP_INDEX - 1);

    return(0);
}

// See gpiolib_gpiod.h.
int
gpiod_backend_active(void)
{
    return(active);
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

static struct gpiod_line_request *
makeRequest(unsigned gpio, GPIO_DIR_T dir, GPIO_PULL_T pull, int value)
{
struct gpiod_line_settings *ls;
struct gpiod_line_config *lc;
struct gpiod_line_request *req;
unsigned offset = gpio;

    ls = gpiod_line_settings_new();
    lc = gpiod_line_config_new();
    req = NULL;

    if( ls && lc )
    {
        gpiod_line_settings_set_direction(ls,
            (dir == DIR_OUTPUT) ? GPIOD_LINE_DIRECTION_OUTPUT
                                : GPIOD_LINE_DIRECTION_INPUT);
        gpiod_line_settings_set_bias(ls,
            (pull == PULL_UP) ? GPIOD_LINE_BIAS_PULL_UP :
            (pull == PULL_DOWN) ? GPIOD_LINE_BIAS_PULL_DOWN
                                : GPIOD_LINE_BIAS_DISABLED);

        if( dir == DIR_OUTPUT )
        {
            gpiod_line_settings_set_output_value(ls,
                value ? GPIOD_LINE_VALUE_ACTIVE : GPIOD_LINE_VALUE_INACTIVE);
        }

        if( gpiod_line_config_add_line_settings(lc, &offset, 1, ls) == 0 )
        {
            req = gpiod_chip_request_lines(chipP, NULL, lc);
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

    return(req);
}

// (Re)requests 'gpio' as dir/pull unless it is already requested that way.
// Returns 0 (and leaves the line unrequested) if the kernel refused.
static int
ensureLine(unsigned gpio, GPIO_DIR_T dir, GPIO_PULL_T pull)
{
GPIOD_LINE_T *lineP = &lines[gpio];
struct gpiod_line_request *req;

    if( lineP->reqP && (lineP->dir == dir) && (lineP->pull == pull) )
    {
        return(1);
    }

    req = makeRequest(gpio, dir, pull, lineP->value);
    if( !req )
    {
        if( lineP->reqP )
        {
            gpiod_line_request_release(lineP->reqP);
            lineP->reqP = NULL;
        }

        if( !warned_io )
        {
            warned_io = 1;
            logMsg("!line %u request failed (%s); the panel is deaf from here on",
                gpio, strerror(errno));
        }

        return(0);
    }

    if( lineP->reqP )
    {
        gpiod_line_request_release(lineP->reqP);
    }

    lineP->reqP = req;
    lineP->dir = dir;
    lineP->pull = pull;
    lineP->have_dir = 1;
    lineP->have_pull = 1;

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
// not expose, so those are said out loud once and dropped.
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

    if( !warned_alt )
    {
        warned_alt = 1;
        logMsg("!fsel %d requested without the register backend; alternate "
            "functions need gpiomem or root", (int)fsel);
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

    if( ensureLine(gpio, DIR_OUTPUT,
            lines[gpio].have_pull ? lines[gpio].pull : PULL_NONE) )
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

// See gpiolib_gpiod.h.
void
gpiod_backend_set(unsigned gpio)
{
    gpiod_backend_set_drive(gpio, DRIVE_HIGH);
}

// See gpiolib_gpiod.h.
void
gpiod_backend_clear(unsigned gpio)
{
    gpiod_backend_set_drive(gpio, DRIVE_LOW);
}

// See gpiolib_gpiod.h.
// An unrequested line is read as an input with the pulls off, matching what
// the register backend reports for a pin still in its reset state.
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

    if( !lineP->reqP && !ensureLine(gpio, DIR_INPUT, PULL_NONE) )
    {
        return(0);
    }

    // v2 returns the level directly: 1/0, or -1 on error.
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
void
gpiod_backend_set_pull(unsigned gpio, GPIO_PULL_T pull)
{
    if( !usable(gpio) )
    {
        return;
    }

    ensureLine(gpio, lines[gpio].have_dir ? lines[gpio].dir : DIR_INPUT, pull);
}

#endif /* HAVE_GPIOD */
