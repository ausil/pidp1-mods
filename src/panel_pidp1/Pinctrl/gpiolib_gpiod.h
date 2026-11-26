/*
 * libgpiod backend for gpiolib.c, compiled in when the build finds the
 * libgpiod development files (pkg-config libgpiod; -DHAVE_GPIOD).
 *
 * This is the GPIO path that works on a distribution kernel: Fedora's
 * aarch64 kernel ships no gpiomem driver and CONFIG_STRICT_DEVMEM forbids
 * mapping the GPIO registers from userspace, so the register-poking backend
 * (gpiolib_init()/gpiolib_mmap()) is dead there and /dev/gpiochipN is the
 * supported interface. gpiolib.c probes this backend first and routes every
 * operation whose semantics the kernel GPIO character device actually has -
 * direction, output value, input level, pull bias - through it while it is
 * active; pin multiplexing (an fsel that is not plain input/output) has no
 * libgpiod equivalent and stays with the register backend, with a warning.
 *
 * Line offsets are used verbatim as legacy BCM GPIO numbers, which holds for
 * both pinctrl-bcm2835 (Pi 0-4) and pinctrl-rp1 (Pi 5, 40-pin header bank) -
 * the two controllers the PiDP-1 panel is wired to.
 *
 * Not built (and not referenced) unless HAVE_GPIOD; gpiolib.c guards its
 * calls the same way, so a tree built without libgpiod behaves exactly as
 * it did before this file existed.
*/
#ifndef GPIOLIB_GPIOD_H
#define GPIOLIB_GPIOD_H

#ifdef HAVE_GPIOD

#include "gpiolib.h"

// Opens the panel's GPIO chip. Auto-selects only a chip whose name or label
// is exactly one of the 40-pin header controllers (pinctrl-bcm2835,
// -bcm2711, -rp1); PIDP1_GPIO_CHIP names the chip ("gpiochip4", a /dev path
// or a chip label) and PIDP1_PANEL_FORCE=1 is the operator's second,
// deliberate yes to a chip that is not a header controller. PIDP1_NO_GPIOD=1
// declines the backend entirely (development escape hatch: forces the
// register path). Returns 1 when a chip was claimed, 0 otherwise.
int gpiod_backend_probe(void);

// 1 once gpiod_backend_probe() has claimed a chip.
int gpiod_backend_active(void);

// The claimed chip's line count (capped at MAX_GPIO_PINS), 0 when inactive.
// gpiolib_init() reports this as the GPIO count when the device tree gave
// it none: an upstream device tree has no /aliases/gpioN for the register
// probe to follow, yet the character device can drive every line.
unsigned gpiod_backend_num_gpios(void);

// Routes the verbose messages through gpiolib's callback.
void gpiod_backend_set_verbose(void (*callback)(const char *));

// The gpio_*() equivalents; same preconditions and return conventions as
// their gpiolib.c twins. 'gpio' is bounds-checked against the chip's line
// count; out-of-range access is ignored like an unknown pin, not fatal.
int gpiod_backend_num_is_valid(unsigned gpio);
int gpiod_backend_get_dir(unsigned gpio);                    // GPIO_DIR_T or DIR_MAX
void gpiod_backend_set_dir(unsigned gpio, GPIO_DIR_T dir);
void gpiod_backend_set_fsel(unsigned gpio, GPIO_FSEL_T fsel);
void gpiod_backend_set_drive(unsigned gpio, GPIO_DRIVE_T drv);
void gpiod_backend_set_multi_drive(const int *gpios, const GPIO_DRIVE_T *drvs, int count);
void gpiod_backend_set(unsigned gpio);
void gpiod_backend_clear(unsigned gpio);
int gpiod_backend_get_level(unsigned gpio);
int gpiod_backend_get_pull(unsigned gpio);                   // GPIO_PULL_T or PULL_MAX
void gpiod_backend_set_pull(unsigned gpio, GPIO_PULL_T pull);

#endif /* HAVE_GPIOD */

#endif /* GPIOLIB_GPIOD_H */
