#!/usr/bin/env bash
# angel-niri with the Snap / Peek / show-desktop patch (window snapping zones, peeking at the
# desktop, Win+D) that the angelOS shell of e5f771c asks for and the author's ce52b4a8 lacks,
# the living pointer cursor_fx (lean, click dip + ring, smear, shadow, size) and the camera that
# follows the pointer (Super+Ctrl+Shift+U); both switched and tuned in Settings → Cursor by the
# shell patch cursor-motion.
# Built from source the way angelOS's own scripts/angel-niri-install.sh does (same source folder,
# same pinned commits), our patch on top, installed beside the author's build and made the
# session's niri from the next login.
#   build-niri.sh          build and switch to it
#   build-niri.sh revert   back to the author's build (from the next login)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PATCHES=("$HERE"/00[0-9][0-9]-*.patch)   # every patch here, in order
SHELL_DIR="$HOME/.config/quickshell/angelos"
PIN="$SHELL_DIR/data/angel-niri.json"
SRC="${XDG_CACHE_HOME:-$HOME/.cache}/angel-niri-src"
LIB="$HOME/.local/lib/angel-niri"
DROPIN="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/niri.service.d/angel-niri.conf"
WANT=ce52b4a8   # the build our patch was written for

pin() { python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$PIN" "$1"; }
use() {
  mkdir -p "${DROPIN%/*}" "$HOME/.local/bin"
  # explicit sync on (0012/0013: NVIDIA has no implicit sync, Xwayland flips need it); a build
  # without our patches (revert) gets no env
  local env=()
  [[ "$1" == *-kit* ]] && env=("# explicit sync (pc-kit 0012/0013); off: delete this line, relogin" "Environment=ANGEL_NIRI_SYNCOBJ=1")
  printf '%s\n' "# angelOS: the session's niri (pc-kit build-niri.sh; back: build-niri.sh revert)" \
    "[Service]" "ExecStart=" "ExecStart=$1 --session" "${env[@]}" >"$DROPIN"
  ln -sfn "$1" "$HOME/.local/bin/niri"
  systemctl --user daemon-reload
  echo "со следующего входа: $1"
}

[[ -f "$PIN" ]] || { echo "нет $PIN — сначала поставь angelOS"; exit 1; }
commit="$(pin commit)"
short="${commit:0:8}"

if [[ "${1:-}" == revert ]]; then
  [[ -x "$LIB/$short/niri" ]] || { echo "нет сборки автора $LIB/$short — запусти angel-niri-install.sh"; exit 1; }
  use "$LIB/$short/niri"; exit 0
fi

if [[ "$short" != "$WANT" ]]; then
  echo "angelOS закреплён на angel-niri $short, а патч писался для $WANT."
  echo "Скорее всего автор уже выпустил новую версию — проверь, есть ли в ней Snap/Peek/показ стола;"
  echo "если есть, этот шаг не нужен. Ничего не меняю."
  exit 0
fi

if ! command -v cargo >/dev/null || ! command -v clang >/dev/null; then
  echo "ставлю Rust и clang для сборки"
  sudo pacman -S --needed --noconfirm rust clang
fi

mkdir -p "$SRC"
for name in angel-smithay angel-niri; do
  if [[ "$name" == angel-niri ]]; then repo="$(pin repo)" rev="$commit"; else repo="$(pin smithay_repo)" rev="$(pin smithay)"; fi
  [[ -d "$SRC/$name/.git" ]] || git clone --quiet "https://github.com/$repo.git" "$SRC/$name"
  git -C "$SRC/$name" fetch --quiet origin
  git -C "$SRC/$name" checkout --quiet --force "$rev"
done

cd "$SRC/angel-niri"
git checkout --quiet -B kit/snap-peek "$commit"
git clean -fdq   # files a previous build or test left (untracked; target/ is ignored and stays)
for patch in "${PATCHES[@]}"; do
  git apply --check "$patch"
  git apply "$patch"
done
echo "собираю angel-niri $short + патчи Snap/Peek, живой курсор и камера (на i5-12400F минут 5–10, лог: $SRC/build.log)"
touch niri-ipc/src/lib.rs   # cargo once kept a stale niri-ipc (no SnapWindow) after a checkout
nice cargo build --release --locked >"$SRC/build.log" 2>&1 || { tail -20 "$SRC/build.log"; exit 1; }
# the build before this one stays as $short-kit-prev (back: ExecStart in the drop-in)
if [[ -x "$LIB/$short-kit/niri" ]]; then rm -rf "$LIB/$short-kit-prev"; mv "$LIB/$short-kit" "$LIB/$short-kit-prev"; fi
mkdir -p "$LIB/$short-kit"
install -m 0755 target/release/niri "$LIB/$short-kit/niri"
"$LIB/$short-kit/niri" validate >/dev/null && echo "конфиг niri принят"
use "$LIB/$short-kit/niri"
