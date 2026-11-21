# Top-level build and packaging for the PiDP-1 software.
#
#   make                    build everything (install/build-all.sh fills bin/)
#   make rpm                RPMs + source RPM into ./dist-rpm
#   make rpmlint            build the RPMs, then check them with rpmlint
#   make clean              clean the source directories
#   make clean-all          also remove bin/'s build products and the drops
#
# Unlike the PiDP-10 tree, the programs build where their own makefiles live:
# the install locations are compiled into them (src/common/pidp1_paths.h) and
# exported by one file for the scripts (bin/pidp1-env.sh), so there is no
# out-of-tree staging to keep straight and no %install sed to drift. That
# also means a PREFIX move is a pidp1_paths.h rebuild (-DPIDP1_STATEDIR=... and
# friends), not a Makefile variable.
#
# Every Makefile in the tree follows one convention: CC ?= cc, CFLAGS ?= the
# default policy for a bare source build, and whatever a directory requires
# (-I paths, -fPIC, defines) appended with +=. rpmbuild exports %optflags into
# the %build environment, so CFLAGS from the environment - the distribution's
# hardening and optimization - reaches every compile and link line, and the
# ?= defaults apply only when nobody set them.

RPM_DIR ?= dist-rpm
WORKTREE ?=

# The set install/build-all.sh builds; clean follows it rather than inventing
# its own list.
CLEANDIRS := src/pdp1 src/panel_pidp1 src/scanpf src/tapevis src/pidp1_test \
             src/pdp1central src/ptytools src/usb_paper_tape \
             src/vpanel_pdp1 src/pdp1_periph \
             Tools/AM1 Tools/AD1 Tools/Drumupdater Tools/Utils Tools/Ovlload \
             Tools/T30dpy Tools/MtoA Tools/Disassembler Tools/Docviewer \
             IOTs/Microtape Tools

.PHONY: all clean clean-all rpm rpmlint

all:
	install/build-all.sh

# bin/'s scripts are tracked; its programs are what build-all.sh put there,
# and clean removes exactly those. (Nothing in the lists below is a tracked
# file - git ls-files bin/ shows only scripts.)
BINPROGS := ad1 am1 asr33tape disassemble docviewer drumlist drumupdater \
            fastload fstool mactoam1 mkmicrotape mkptyfio mkptyfl mtp ovlload \
            pdp1audio t30dpy macro1_1 scanpf tapevis pidp1_test pdp1central \
            pdp1 pdp1_periph pdp1_periphES pdp1_usb_monitor vpanel_pdp1 \
            panel_pidp1 pdpsrv

clean:
	@for d in $(CLEANDIRS); do \
	    [ -f $$d/Makefile ] && $(MAKE) -C $$d clean || true; done
	$(MAKE) -C IOTs clean

clean-all: clean
	rm -f $(addprefix bin/,$(BINPROGS)) bin/binaries-for-*.tar.gz
	rm -rf dist dist-rpm

# packaging/build-rpm.sh stages the sources in dist/ and drops the products
# flat in $(RPM_DIR): _sourcedir/_rpmdir/_srcrpmdir point there and
# _rpmfilename keeps the arch subdirectory out of the path; rpmbuild's scratch
# stays in ~/rpmbuild - the tree holds no BUILD/ or SOURCES/. WORKTREE=yes
# packages the tree as it stands - while work is uncommitted, the default HEAD
# snapshot lints code you did not write.
rpm:
	packaging/build-rpm.sh $(if $(filter yes,$(WORKTREE)),--worktree) $(RPM_DIR)

# Lint the RPMs, no bare-spec argument: the sysusers and tmpfiles macros read
# Source1/Source2 at parse time, which only resolves inside the staged build
# tree - linting the bare spec manufactures false errors. Exceptions live in
# packaging/rpmlint.toml with a reason each, not in someone's scrollback.
rpmlint: rpm
	rpmlint -c packaging/rpmlint.toml $(RPM_DIR)/*.rpm
