#!/usr/bin/env bash
# serp-skin: compile-check the skin on a COPY of the live shell (nothing runs, nothing live changes)
#   check.sh   → prints qml-check's verdict for the copy with the patch applied
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d /tmp/serpchk.XXXXXX); trap 'rm -rf "$T"' EXIT
rsync -a --exclude '*.angelos-orig' --exclude graphify-out "$HOME/.config/quickshell/angelos/" "$T/shell/"
ANGELOS_SHELL="$T/shell" python3 "$HERE/apply.py" >/dev/null || { echo "apply failed"; exit 2; }
"$HOME/.config/quickshell/angelos/scripts/qml-check.sh" "$T/shell" 2>&1 | grep -v -E '^\s*$' | tail -40
