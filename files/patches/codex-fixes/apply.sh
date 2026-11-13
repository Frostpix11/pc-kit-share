#!/bin/bash
# Патчи Кодекса: исправления багов angelOS (шелл e5f771c), которых у автора пока нет.
#   fix-golden-gate-spotlight-blur  Golden Gate: размытие под Spotlight ездит отдельно от панели (StartOverlay.qml)
#   fix-golden-gate-bar-halo        Golden Gate: нимб сдвигает верхнюю панель вниз на 42 px (MacMenuBar, HaloWindow)
#   fix-win-d-repeat-animation      Win+D: анимации сворачивания запускаются повторно (MacMinimizeFx.qml)
#   fix-golden-gate-genie           Golden Gate: Genie-сворачивание прозрачное (деление на 0 в genie.vert + .qsb)
# Каждый ставится, только если код автора совпадает с тем, под который он сделан (git apply --check).
# Если автор файл поменял — патч пропускается: скорее всего, баг уже исправлен у автора.
#   apply.sh          поставить, что встаёт (оригиналы -> orig/<stamp>/), включить сторож
#   apply.sh --wait   то же, после конца обновления angelOS (так зовёт kit-patch-codex.service)
#   apply.sh revert   снять, выключить сторож
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SH=.config/quickshell/angelos
PATCHES=(fix-golden-gate-spotlight-blur.patch fix-golden-gate-bar-halo.patch fix-win-d-repeat-animation-e5f771c.patch fix-golden-gate-genie.patch)
FILES=(modules/bar/StartOverlay.qml modules/mac/MacMenuBar.qml modules/halo/HaloWindow.qml modules/mac/MacMinimizeFx.qml shaders/genie.vert shaders/genie.vert.qsb)
if [ "${1:-}" = --wait ] && [ -z "${KIT_RUNNER:-}" ]; then   # kit waits for the updater itself
  while pgrep -f "[d]otfiles-update.sh|[A]ngelOS-Dotfiles/install.sh|[i]nstaller/steps" >/dev/null; do sleep 5; done
  sleep 3
fi
restart_shell() { "$HERE/../restart-shell.sh"; }  # kit: общий отложенный перезапуск
ga() { git -C "$HOME" apply "$@" 2>/dev/null; }
changed=0
if [ "${1:-}" = revert ]; then
  systemctl --user disable --now kit-patch-codex.path 2>/dev/null || true
  for p in "${PATCHES[@]}"; do
    ga --reverse --check "$HERE/$p" && ga --reverse "$HERE/$p" && { echo "снят ${p%.patch}"; changed=1; }
  done
  [ $changed = 1 ] && restart_shell
  echo "откатил"; exit 0
fi
[ "${1:-}" = --wait ] || systemctl --user enable --now kit-patch-codex.path 2>/dev/null || true
stamp=$(date +%Y%m%d-%H%M%S)
for p in "${PATCHES[@]}"; do
  n=${p%.patch}
  if ga --reverse --check "$HERE/$p"; then echo "$n: уже стоит"
  elif ga --check "$HERE/$p"; then
    if [ $changed = 0 ]; then
      mkdir -p "$HERE/orig/$stamp"
      for f in "${FILES[@]}"; do [ -f "$HOME/$SH/$f" ] && cp -p "$HOME/$SH/$f" "$HERE/orig/$stamp/"; done
    fi
    ga "$HERE/$p" && { echo "$n: поставлен"; changed=1; }
  else echo "$n: код автора изменился — пропускаю (скорее всего, автор уже исправил)"
  fi
done
[ $changed = 1 ] && restart_shell
exit 0
