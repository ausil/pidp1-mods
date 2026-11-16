#!/usr/bin/bash
# SPDX-License-Identifier: MIT
#
# build-rpm.sh - build the RPMs from this tree.
#
#   packaging/build-rpm.sh [topdir]                    default topdir: ./dist-rpm
#   packaging/build-rpm.sh --worktree [topdir]         package the work tree
#   packaging/build-rpm.sh --srpm-only [topdir]        just the SRPM (for COPR)
#
# By default the source tarball is a `git archive` of HEAD: what ships is what
# is committed, the only version of the project reproducible from the
# repository alone. A dirty work tree is said out loud, because silently
# building an RPM nobody can rebuild is how a package ends up containing a fix
# that exists in one person's checkout.
#
# --worktree packages the tree as it stands instead (tracked modifications and
# untracked files, minus what .gitignore excludes): for testing a change
# before committing it, not for anything that leaves the machine.
#
# Source0 is the whole tree. It holds no prebuilt binaries: the compiled
# programs are built by install/build-all.sh from the same sources, and the
# precompiled binaries-for-<arch>.tar.gz drop lives only in a built bin/,
# which .gitignore keeps out of the archive. web_pdp1's one third-party Go
# package is vendored so the build needs no network.

set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/.." && pwd)
cd "$root"

worktree=0
srpm_only=0
while [ "${1:-}" = "--worktree" ] || [ "${1:-}" = "--srpm-only" ]; do
	case "$1" in
	    --worktree)  worktree=1 ;;
	    --srpm-only) srpm_only=1 ;;
	esac
	shift
done
top=$(realpath -m "${1:-dist-rpm}")

spec=$here/pidp1-mods.spec
version=$(sed -n 's/^Version:[[:space:]]*\([0-9.]*\).*/\1/p' "$spec" | head -1)
[ -n "$version" ] || { echo "build-rpm: cannot read Version from the spec" >&2; exit 1; }
srcdate=$(sed -n 's/^%global srcdate \([0-9]*\).*/\1/p' "$spec" | head -1)
[ -n "$srcdate" ] || { echo "build-rpm: cannot read srcdate from the spec" >&2; exit 1; }
name=pidp1-mods
topdir_prefix=$name-$version-$srcdate

# make_tarball DEST PREFIX PATHSPEC...
#   PREFIX "" means the archive holds bare relative paths.
make_tarball()
{
	local dest=$1 prefix=$2; shift 2

	if [ "$worktree" = 1 ]; then
		# git ls-files keeps .gitignore in force, so the build products in
		# bin/, dist-rpm/ and dist/ stay out the same way they do for git.
		git ls-files -z --cached --others --exclude-standard -- "$@" |
		    tar --format=gnu --null ${prefix:+--transform="s|^|$prefix/|S"} -cf - -T - |
		    gzip > "$dest"
	else
		git archive --format=tar ${prefix:+--prefix="$prefix/"} HEAD -- "$@" |
		    gzip > "$dest"
	fi
}

if [ "$worktree" = 1 ]; then
	echo "build-rpm: packaging the WORK TREE (uncommitted changes included;"
	echo "build-rpm: nobody but you can rebuild this)" >&2
elif [ -n "$(git status --porcelain)" ]; then
	echo "build-rpm: WARNING: work tree is dirty; HEAD is being packaged and" >&2
	echo "build-rpm: your uncommitted work is NOT in it. --worktree to include it." >&2
	git status --short | head -20 >&2
fi

# Two directories: the sources go to dist/ (the _sourcedir), the products land
# flat in $top. No _topdir is set, so no tree of SOURCES/BUILD/BUILDROOT
# appears in either - rpmbuild's scratch stays in ~/rpmbuild. _rpmfilename
# keeps the arch subdirectory out of the path; the %% are load-bearing there,
# deferring NAME to packaging time where rpm rebinds it per package, so the
# main package and -debuginfo cannot overwrite each other.
dist=${DIST_DIR:-$root/dist}
mkdir -p "$top" "$dist"

# Source1/2: staged copies of the sysusers and tmpfiles fragments. The
# create_package macros read them at spec-parse time, before %prep, so only a
# file already in _sourcedir can be read. They are cp'd fresh from
# packaging/systemd/ on every build, which keeps them from drifting.
cp "$here/systemd/sysusers.d/pidp1-mods.conf" "$dist/pidp1-mods.sysusers.conf"
cp "$here/systemd/tmpfiles.d/pidp1-mods.conf" "$dist/pidp1-mods.tmpfiles.conf"

# Source0 is named by the spec itself (rpmspec -P reads it with _sourcedir
# staged, so the parse-time reads stay quiet); this script and a bare
# rpmbuild -bs then want exactly the same file. The archive prefix is
# %{name}-%{version}-%{srcdate}, which is what %autosetup -n digs out.
tarball=$(rpmspec -P --define "_sourcedir $dist" "$spec" |
          sed -n 's/^Source0:[[:space:]]*//p' | head -1)
[ -n "$tarball" ] || { echo "build-rpm: cannot read Source0 from the spec" >&2; exit 1; }
make_tarball "$dist/$tarball" "$topdir_prefix" .

rpmbuild -b$([ "$srpm_only" = 1 ] && echo s || echo a) \
    --define "_sourcedir $dist" \
    --define "_rpmdir $top" --define "_srcrpmdir $top" \
    --define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" \
    "$spec"

if [ "$srpm_only" = 1 ]; then
	ls -1 "$top"/*.src.rpm
else
	echo "RPMs: $top"
fi
