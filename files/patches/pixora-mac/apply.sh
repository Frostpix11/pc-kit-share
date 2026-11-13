#!/bin/bash
# Патч angelOS: мак-режим (Golden Gate) с выключенными «значками MacTahoe» берёт свои иконки
# пользователя (angelos-folders-b → pixora) вместо Adwaita: GTK, Qt и Strata (как в пиксельной теме).
# Куски — в patch.py (services/ThemeExport.qml, scripts/goldengate.py, qt-theme.py, folder-tint.py,
# modules/mac/MacDock.qml: кнопки дока Приложения/Настройки/Загрузки/Корзина из темы — angelos-dock-*).
# Ещё следит за иконками Codex в pixora под именами приложений (Helium, Freshgram, Claude, qThrone, Strata, кнопки дока):
# если обновление pixora их снесло — кладёт из ~/.local/share/angelos-kit/icons.
#   apply.sh          применить (оригиналы -> orig/<stamp>/), включить сторож
#   apply.sh --wait   то же, после конца обновления angelOS (так зовёт kit-patch-pixora.service)
#   apply.sh revert   вернуть как у автора, выключить сторож
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SH="$HOME/.config/quickshell/angelos"
FILES=(services/ThemeExport.qml scripts/goldengate.py scripts/qt-theme.py scripts/folder-tint.py modules/mac/MacDock.qml)
PAL="$HOME/.cache/angelos/palette.json"

if [ "${1:-}" = --wait ] && [ -z "${KIT_RUNNER:-}" ]; then   # kit waits for the updater itself
  while pgrep -f "[d]otfiles-update.sh|[A]ngelOS-Dotfiles/install.sh|[i]nstaller/steps" >/dev/null; do sleep 5; done
  sleep 3
fi

# хуки темы заново по текущей палитре (как шелл после смены темы)
rehook() {
  [ -f "$PAL" ] || return 0
  for s in goldengate.py qt-theme.py folder-tint.py; do python3 "$SH/scripts/$s" "$PAL" >/dev/null 2>&1 || echo "хук $s: ошибка"; done
  echo "хуки темы перезапущены"
}
# QML подхватывается только перезапуском шелла; док читает иконки тоже только при старте
restart_shell() { "$HERE/../restart-shell.sh"; }  # kit: общий отложенный перезапуск

codex_icons() {
  local A="$HOME/.local/share/icons/pixora/scalable/apps" S="$HOME/.local/share/angelos-kit/icons" n=0
  [ -d "$A" ] || return 0
  for pair in helium:helium helium:helium-browser freshgram:freshgram freshgram:freshGram freshgram:io.github.snowy-fluffy.freshgram \
      claude:claude-desktop claude:com.anthropic.Claude claude:claude qthrone:qthrone qthrone:qThrone strata:io.github.lgse.Strata strata:strata \
      dockapps:angelos-dock-apps docksettings:angelos-dock-settings dockdownloads:angelos-dock-downloads docktrash:angelos-dock-trash docktrashfull:angelos-dock-trash-full hwloc:hwloc; do
    src="$S/${pair%%:*}.svg" dst="$A/${pair##*:}.svg"
    [ -f "$src" ] && ! cmp -s "$src" "$dst" && { rm -f "$dst"; cp "$src" "$dst"; n=$((n+1)); }
  done
  # у pixora-dark свой кэш (её scalable — ссылка на pixora): GTK без него новых иконок не видит
  [ $n -gt 0 ] && { for t in pixora pixora-dark; do gtk-update-icon-cache -f -q "$HOME/.local/share/icons/$t" 2>/dev/null; done; echo "иконки Codex: вернул $n"; }
  return 0
}

if [ "${1:-}" = revert ]; then
  systemctl --user disable --now kit-patch-pixora.path 2>/dev/null || true
  out=$(python3 "$HERE/patch.py" revert); echo "$out"
  rehook; grep -q changed-qml <<<"$out" && restart_shell
  echo "откатил"; exit 0
fi

[ "${1:-}" = --wait ] || systemctl --user enable --now kit-patch-pixora.path 2>/dev/null || true
if ! python3 "$HERE/patch.py" check >/dev/null; then
  stamp=$(date +%Y%m%d-%H%M%S); mkdir -p "$HERE/orig/$stamp"
  for f in "${FILES[@]}"; do [ -f "$SH/$f" ] && cp -p "$SH/$f" "$HERE/orig/$stamp/"; done
  out=$(python3 "$HERE/patch.py" apply); rc=$?; echo "$out"
  [ $rc -eq 0 ] && echo "применил ($stamp)" || echo "ВНИМАНИЕ: не всё встало (см. выше)"
  codex_icons; rehook; grep -q changed-qml <<<"$out" && restart_shell
else
  echo "уже применён"; codex_icons
fi
exit 0
