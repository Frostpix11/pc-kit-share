#!/bin/bash
# Патч angelOS «dock-spacing»: в Golden Gate настраиваются отступы Дока —
# промежуток между значками и поля вокруг них (Настройки → Golden Gate → Dock).
# Куски — в patch.py (SettingsSchema, GoldenGate, MacDock, catalog/Mac).
#   apply.sh          применить (оригиналы -> orig/<stamp>/), включить сторож
#   apply.sh --wait   то же, после конца обновления angelOS (так зовёт kit-patch-dockspacing.service)
#   apply.sh revert   вернуть как у автора, выключить сторож
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SH="$HOME/.config/quickshell/angelos"
FILES=(config/SettingsSchema.qml services/GoldenGate.qml modules/mac/MacDock.qml modules/settings/catalog/Mac.qml)
if [ "${1:-}" = --wait ] && [ -z "${KIT_RUNNER:-}" ]; then   # kit waits for the updater itself
  while pgrep -f "[d]otfiles-update.sh|[A]ngelOS-Dotfiles/install.sh|[i]nstaller/steps" >/dev/null; do sleep 5; done
  sleep 9   # after mac-tint, pixora-mac and skin-morph, which edit the same files
fi
restart_shell() { "$HERE/../restart-shell.sh"; }  # kit: общий отложенный перезапуск
if [ "${1:-}" = revert ]; then
  systemctl --user disable --now kit-patch-dockspacing.path 2>/dev/null || true
  out=$(python3 "$HERE/patch.py" revert); echo "$out"; grep -q changed-qml <<<"$out" && restart_shell
  echo "откатил"; exit 0
fi
[ "${1:-}" = --wait ] || systemctl --user enable --now kit-patch-dockspacing.path 2>/dev/null || true
if ! python3 "$HERE/patch.py" check >/dev/null; then
  stamp=$(date +%Y%m%d-%H%M%S); mkdir -p "$HERE/orig/$stamp"
  for f in "${FILES[@]}"; do [ -f "$SH/$f" ] && cp -p "$SH/$f" "$HERE/orig/$stamp/"; done
  out=$(python3 "$HERE/patch.py" apply); rc=$?; echo "$out"
  [ $rc -eq 0 ] && echo "применил ($stamp)" || echo "ВНИМАНИЕ: не всё встало (см. выше)"
  grep -q changed-qml <<<"$out" && restart_shell
else
  echo "уже применён"
fi
exit 0
