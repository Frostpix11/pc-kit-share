#!/usr/bin/env bash
# serp-skin dev stand: a nested niri in a window of its own (output "winit"), and inside it a copy
# of the live shell with the patch applied, sandboxed HOME (like angelOS's perf.py stand),
# Golden Gate + look=serp. The live desktop is not touched.
#   stand.sh start | shot [out.png] | msg <niri msg args…> | ipc <angelos ipc args…> | log | stop
#   SERP_LOOK=mac stand.sh start   — the same stand with the plain Golden Gate look
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ST=/tmp/aos-serp
LIVE=$HOME/.config/quickshell/angelos
PARENT_RT=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}

nested_env() {
  local wd sock
  wd=$(cd "$ST/rt" && ls wayland-* 2>/dev/null | grep -v lock | head -1)
  sock=$(ls "$ST"/rt/niri.*.sock 2>/dev/null | head -1)
  echo "WAYLAND_DISPLAY=$ST/rt/$wd NIRI_SOCKET=$sock"
}

case "${1:-start}" in
start)
  "$0" stop >/dev/null 2>&1 || true
  mkdir -p "$ST"/home/.config/angelos "$ST"/home/.config/niri "$ST"/home/.local/share "$ST"/home/.cache "$ST"/home/.local/state "$ST"/rt
  chmod 700 "$ST"/rt
  # the nested niri: the live look (layout, animations, angelOS rules), no autostart, no binds
  cat >"$ST/niri.kdl" <<EOF
include "$HOME/.config/niri/cfg/layout.kdl"
include "$HOME/.config/niri/cfg/animation.kdl"
include "$HOME/.config/niri/angelos.kdl"
hotkey-overlay { skip-at-startup; }
prefer-no-csd
EOF
  env XDG_RUNTIME_DIR="$ST/rt" WAYLAND_DISPLAY="$PARENT_RT/${WAYLAND_DISPLAY:-wayland-1}" \
    setsid niri -c "$ST/niri.kdl" >"$ST/niri.log" 2>&1 &
  echo $! >"$ST/niri.pid"
  for _ in $(seq 50); do ls "$ST"/rt/niri.*.sock >/dev/null 2>&1 && break; sleep 0.2; done
  # the shell copy + patch
  rsync -a --delete --exclude '*.angelos-orig' "$LIVE"/ "$ST"/shell/
  ANGELOS_SHELL="$ST"/shell python3 "$HERE"/apply.py
  for d in fonts angelos; do [ -e "$HOME/.local/share/$d" ] && ln -sfn "$HOME/.local/share/$d" "$ST/home/.local/share/$d"; done
  cp "$HOME/.config/angelos/save.json" "$ST/home/.config/angelos/" 2>/dev/null || true
  cp -r "$HOME/.config/niri/cfg" "$ST/home/.config/niri/" 2>/dev/null || true
  python3 - "$ST" <<'EOF'
import json, os, sys
st = sys.argv[1]
s = json.load(open(os.path.expanduser("~/.config/angelos/settings.json")))
s.setdefault("stream", {})["auto"] = False
y = s.setdefault("y2k", {}); y["boot"] = False; y["sounds"] = False
s.setdefault("setup", {})["complete"] = True
s.setdefault("system", {})["primaryScreen"] = "winit"
s.setdefault("updates", {})["autoCheck"] = False
s.setdefault("settingsUi", {})["skin"] = "goldengate"
s.setdefault("mac", {})["look"] = os.environ.get("SERP_LOOK", "serp")
s["mac"]["sounds"] = False
s.setdefault("game", {})["enabled"] = False
if os.environ.get("HALO_OFF"): s.setdefault("halo", {})["enabled"] = False
json.dump(s, open(st + "/home/.config/angelos/settings.json", "w"))
EOF
  eval "$(nested_env)"
  env -i PATH="$PATH" LANG="${LANG:-C.UTF-8}" HOME="$ST/home" USER="$USER" \
    XDG_CONFIG_HOME="$ST/home/.config" XDG_STATE_HOME="$ST/home/.local/state" \
    XDG_CACHE_HOME="$ST/home/.cache" XDG_DATA_HOME="$ST/home/.local/share" \
    XDG_DATA_DIRS="${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" XDG_RUNTIME_DIR="$ST/rt" \
    PIPEWIRE_RUNTIME_DIR="$PARENT_RT" PULSE_RUNTIME_PATH="$PARENT_RT/pulse" \
    WAYLAND_DISPLAY="$WAYLAND_DISPLAY" NIRI_SOCKET="$NIRI_SOCKET" \
    QT_QPA_PLATFORM=wayland QT_QPA_PLATFORMTHEME=gtk3 QT_WAYLAND_DISABLE_WINDOWDECORATION=1 \
    ANGELOS_DEV=1 ANGELOS_SCREENS=winit QS_NO_RELOAD_POPUP=1 ANGELOS_PERF_STAND=1 \
    setsid dbus-run-session -- quickshell -p "$ST/shell" >"$ST/log" 2>&1 &
  echo $! >"$ST/pid"
  # two windows on desk 1 and one on desk 2: occupied pills to look at
  for i in 1 2; do env -i PATH="$PATH" HOME="$HOME" XDG_RUNTIME_DIR="$ST/rt" WAYLAND_DISPLAY="$WAYLAND_DISPLAY" setsid foot >/dev/null 2>&1 & done
  echo "stand started; niri log $ST/niri.log, shell log $ST/log"
  ;;
shot)
  eval "$(nested_env)"
  out=${2:-$ST/shot.png}
  WAYLAND_DISPLAY=$WAYLAND_DISPLAY grim "$out"
  echo "$out"
  ;;
msg)
  shift; eval "$(nested_env)"
  NIRI_SOCKET=$NIRI_SOCKET niri msg "$@"
  ;;
ipc)
  shift
  env XDG_RUNTIME_DIR="$ST/rt" HOME="$ST/home" quickshell ipc -p "$ST/shell" call "$@"
  ;;
log) tail -n "${2:-60}" "$ST/log" ;;
stop)
  for p in pid niri.pid; do
    [ -f "$ST/$p" ] && { kill -- -"$(cat "$ST/$p")" 2>/dev/null || kill "$(cat "$ST/$p")" 2>/dev/null || true; }
  done
  sleep 0.5
  rm -rf "$ST"
  echo stopped
  ;;
esac
