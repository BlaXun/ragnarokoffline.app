#!/usr/bin/env bash
# Build the pre-renewal rAthena test servers (packetver 20221005) inside the
# alpine toolchain image, the way containers/rathena/Dockerfile does.
#   ./build.sh          incremental make (after editing sources in $RIG/rathena)
#   ./build.sh clean    make clean + configure + full build
set -euo pipefail
RIG="$(cd "$(dirname "$0")" && pwd)"
# One build/up at a time: two makes in the same tree corrupt each other's objects.
if [ -z "${RIG_LOCKED:-}" ]; then
	exec 9>"$RIG/.lock"
	flock -n 9 || { echo "waiting for another build.sh/up.sh on this rig to finish..."; flock 9; }
	export RIG_LOCKED=1
fi
PACKETVER="${PACKETVER:-20221005}"
# Parallel jobs; full -j$(nproc) has been OOM-killed (cc1plus ~0.8 GB each) on this 15 GB host.
JOBS="${JOBS:-8}"
docker image inspect rorig-build >/dev/null 2>&1 || docker build -q -t rorig-build "$RIG/docker"
docker run --rm --user "$(id -u):$(id -g)" -v "$RIG/rathena:/rathena" -w /rathena rorig-build bash -c "
	set -e
	if [ '${1:-}' = clean ] || [ ! -f Makefile ]; then
		[ -f Makefile ] && make clean >/dev/null || true
		./configure --enable-packetver=$PACKETVER --enable-prere >/dev/null
	fi
	make -j$JOBS server
	grep -qa 'npc/pre-re/scripts_main.conf' map-server || { echo 'map-server is not pre-re' >&2; exit 1; }
	echo 'build ok: pre-re, packetver $PACKETVER'
"
