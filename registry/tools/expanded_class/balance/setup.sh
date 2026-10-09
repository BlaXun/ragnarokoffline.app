#!/usr/bin/env bash
# Prepare the balance rig: a pre-renewal rAthena (packetver 20221005) at the
# commit config/VENDOR_PINS pins, cloned into ./rathena and built in a container.
#
#   ./setup.sh [rathena checkout]
#
# The checkout to clone from defaults to vendor/rathena; ../rathena (the fork
# checkout beside this repo) works as well. Needs docker. Run it again after the
# pin moves: it checks the new commit out and rebuilds.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
PIN="$(awk '$1 == "rathena" { print $3 }' "$ROOT/config/VENDOR_PINS")"
[ -n "$PIN" ] || { echo "no rathena pin in config/VENDOR_PINS" >&2; exit 1; }
SRC="$(cd "${1:-$ROOT/vendor/rathena}" && pwd)"
if [ ! -d "$HERE/rathena/.git" ]; then
	git clone -q "$SRC" "$HERE/rathena"
fi
git -C "$HERE/rathena" fetch -q "$SRC" "$PIN" 2>/dev/null || true
git -C "$HERE/rathena" checkout -q "$PIN"
echo "rathena at $(git -C "$HERE/rathena" log --oneline -1)"
"$HERE/build.sh" clean
