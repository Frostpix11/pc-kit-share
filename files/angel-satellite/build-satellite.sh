#!/usr/bin/env bash
# pc-kit: angel-satellite (xwayland-satellite of angelOS) + our patches: 0002 a window niri suspends gets
# _NET_WM_STATE_HIDDEN (X11 apps stop drawing when unseen); 0001-hold-window-size:
# `_ANGEL_SATELLITE_HOLD WxH` on a fullscreen X window keeps it at the game's size and lets the
# compositor stretch it smoothly (CS2 4:3 without its nearest-pixel self-stretch). The helper that
# sets it: ~/.local/bin/celestia-hold (celestia-run HOLD=). Built beside the author's, made the one
# in ~/.local/bin; back: ln -sfn ~/.local/lib/angel-satellite/<commit>/xwayland-satellite ~/.local/bin/
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PIN="$HOME/.config/quickshell/angelos/data/angel-niri.json"
SRC="${XDG_CACHE_HOME:-$HOME/.cache}/angel-niri-src/angel-satellite"
LIB="$HOME/.local/lib/angel-satellite"
WANT=42184a85
pin() { python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$PIN" "$1"; }
commit="$(pin satellite_commit)"; short="${commit:0:8}"
[[ "$short" == "$WANT" ]] || { echo "angelOS закреплён на angel-satellite $short, патч писался для $WANT — перенеси патч"; exit 0; }
command -v cargo >/dev/null || sudo pacman -S --needed --noconfirm rust clang
[[ -d "$SRC/.git" ]] || git clone --quiet "https://github.com/$(pin satellite_repo).git" "$SRC"
git -C "$SRC" fetch --quiet origin; git -C "$SRC" checkout --quiet --force -B kit/hold "$commit"
for patch in "$HERE"/00[0-9][0-9]-*.patch; do git -C "$SRC" apply --check "$patch" && git -C "$SRC" apply "$patch"; done
(cd "$SRC" && nice cargo build --release --locked >"$SRC/build.log" 2>&1) || { tail -20 "$SRC/build.log"; exit 1; }
if [[ -x "$LIB/$short-kit/xwayland-satellite" ]]; then rm -rf "$LIB/$short-kit-prev"; mv "$LIB/$short-kit" "$LIB/$short-kit-prev"; fi
mkdir -p "$LIB/$short-kit"; install -m 0755 "$SRC/target/release/xwayland-satellite" "$LIB/$short-kit/xwayland-satellite"
ln -sfn "$LIB/$short-kit/xwayland-satellite" "$HOME/.local/bin/xwayland-satellite"
echo "angel-satellite $short-kit: со следующего входа"
