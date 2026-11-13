#!/bin/bash
# Патч angelOS: курсор мак-режима (Golden Gate) — angelOS Mac Pixel: курсоры macOS (по мотивам
# ful1e5/apple_cursor, GPL-3.0), перерисованные вручную пиксель-артом 12x12, как angelOS Pixel.
# Тема готовая лежит в ~/.local/share/angelos-kit/cursor-mac (там же build.py + designs.py), ставится в ~/.local/share/icons/angelOS-MacPixel.
# Кусок — в patch.py (services/Cursors.qml: macTheme).
#   apply.sh          применить (оригинал -> orig/<stamp>/), собрать тему если нет, включить сторож
#   apply.sh --wait   то же, после конца обновления angelOS (так зовёт kit-patch-maccursor.service)
#   apply.sh revert   вернуть как у автора (тема остаётся, просто не используется), выключить сторож
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
F="$HOME/.config/quickshell/angelos/services/Cursors.qml"
T="$HOME/.local/share/icons/angelOS-MacPixel"
if [ "${1:-}" = --wait ] && [ -z "${KIT_RUNNER:-}" ]; then   # kit waits for the updater itself
  while pgrep -f "[d]otfiles-update.sh|[A]ngelOS-Dotfiles/install.sh|[i]nstaller/steps" >/dev/null; do sleep 5; done
  sleep 3
fi
restart_shell() { "$HERE/../restart-shell.sh"; }  # kit: общий отложенный перезапуск
if [ "${1:-}" = revert ]; then
  systemctl --user disable --now kit-patch-maccursor.path 2>/dev/null || true
  out=$(python3 "$HERE/patch.py" revert); echo "$out"; grep -q changed-qml <<<"$out" && restart_shell
  echo "откатил"; exit 0
fi
[ "${1:-}" = --wait ] || systemctl --user enable --now kit-patch-maccursor.path 2>/dev/null || true
if [ ! -f "$T/cursors/left_ptr" ]; then
  mkdir -p "$(dirname "$T")" && cp -a "$HOME/.local/share/angelos-kit/cursor-mac/angelOS-MacPixel" "$(dirname "$T")/" && echo "тема angelOS-MacPixel поставлена"
fi
if ! python3 "$HERE/patch.py" check; then
  stamp=$(date +%Y%m%d-%H%M%S); mkdir -p "$HERE/orig/$stamp"; cp -p "$F" "$HERE/orig/$stamp/"
  out=$(python3 "$HERE/patch.py" apply); echo "$out"; echo "применил ($stamp)"
  grep -q changed-qml <<<"$out" && restart_shell
else
  echo "уже применён"
fi
exit 0
