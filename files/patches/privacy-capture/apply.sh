#!/bin/bash
# Патч angelOS: режим приватности (Mod+Shift+X) прячет окна из списка не только на стриме,
# но и на любой записи и скриншотах: block-out-from "screencast" -> "screen-capture" в правиле окон.
# "screencast" ловит только порталы (OBS, стрим); запись angelOS (wf-recorder) и grim шли мимо.
# Запись области (Mod+Shift+R): куски rec/NN-old|new.txt в niri-record-region + rec-switch.py —
# на рабочем столе wf-recorder (приватность работает), в полноэкранной игре gpu-screen-recorder.
# Настройки → Скриншоты и запись → «Приватность в записи экрана» (settings.py; выкл — как у автора).
#   apply.sh          применить (оригинал -> orig/<stamp>/)
#   apply.sh --wait   то же, после конца обновления angelOS (так зовёт kit-patch-privacy.service)
#   apply.sh revert   вернуть как у автора
set -euo pipefail
F="$HOME/.local/bin/niri-cast-privacy"
HERE="$(cd "$(dirname "$0")" && pwd)"
OLD='            lines.append('"'"'    match app-id=r#"^%s$"#'"'"' % re.sub(r"([\\.+*?()|\[\]{}^$])", r"\\\1", a["id"]))
        lines.append('"'"'    block-out-from "screencast"'"'"')'
NEW='            lines.append('"'"'    match app-id=r#"^%s$"#'"'"' % re.sub(r"([\\.+*?()|\[\]{}^$])", r"\\\1", a["id"]))
        lines.append('"'"'    block-out-from "screen-capture"'"'"')  # kit-patch: и на записи/скриншотах, не только на стриме'
if [ "${1:-}" = --wait ] && [ -z "${KIT_RUNNER:-}" ]; then   # kit waits for the updater itself
  while pgrep -f "[d]otfiles-update.sh|[A]ngelOS-Dotfiles/install.sh|[i]nstaller/steps" >/dev/null; do sleep 5; done
  sleep 3
fi
rep() { python3 - "$F" "$1" "$2" <<'PY'
import sys
p, a, b = sys.argv[1:]
s = open(p).read()
if a in s:
    open(p, "w").write(s.replace(a, b, 1)); print("заменено")
PY
}
# запись области (Mod+Shift+R): при включённой приватности wf-recorder вместо gpu-screen-recorder
R="$HOME/.local/bin/niri-record-region"
rec() {  # rec apply|revert — the pieces in rec/NN-old.txt → rec/NN-new.txt
  [ -f "$R" ] || { echo "нет $R"; return 0; }
  python3 - "$R" "$HERE/rec" "$1" <<'PY'
import sys
from pathlib import Path
p, d, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
s = p.read_text()
pairs = [(f.read_text(), f.with_name(f.name.replace("-old", "-new")).read_text()) for f in sorted(d.glob("*-old.txt"))]
t, bad = s, 0
if mode == "revert":
    for old, new in reversed(pairs):
        if new in t:
            t = t.replace(new, old, 1)
else:
    for old, new in pairs:
        if new in t:
            continue
        if t.count(old) == 1:
            t = t.replace(old, new, 1)
        else:
            bad += 1
if bad:
    print(f"ВНИМАНИЕ: niri-record-region у автора изменился — {bad} из {len(pairs)} кусков не нашлось, запись не тронута")
elif t != s:
    p.write_text(t); print("запись: " + ("откатил" if mode == "revert" else "применил"))
else:
    print("запись: " + ("нечего откатывать" if mode == "revert" else "уже применён"))
PY
  bash -n "$R" || echo "ВНИМАНИЕ: niri-record-region не проходит bash -n"
}
# галочка в Настройках (QML): шелл перезапускается один раз на всю пачку патчей
settings() {
  local out; out=$(python3 "$HERE/settings.py" "$1") || true
  [ -n "$out" ] && echo "$out" | grep -v changed-qml
  if grep -q changed-qml <<<"$out"; then "$HERE/../restart-shell.sh" || true; fi
}
# включённый режим переписать по новому правилу (штатно: off -> on)
refresh() {
  if "$F" status | python3 -c 'import json,sys; sys.exit(0 if json.load(sys.stdin)["on"] else 1)'; then
    "$F" off && "$F" on && echo "правило переписано"
  fi
}
if [ "${1:-}" = revert ]; then
  systemctl --user disable --now kit-patch-privacy.path 2>/dev/null || true
  rep "$NEW" "$OLD"; refresh; rec revert; settings revert; echo "откатил"; exit 0
fi
[ "${1:-}" = --wait ] || systemctl --user enable --now kit-patch-privacy.path 2>/dev/null || true
rec apply
settings apply
[ -f "$F" ] || { echo "нет $F"; exit 0; }
if python3 -c 'import sys; sys.exit(0 if open(sys.argv[1]).read().find(sys.argv[2])>=0 else 1)' "$F" "$OLD"; then
  stamp=$(date +%Y%m%d-%H%M%S); mkdir -p "$HERE/orig/$stamp"; cp -p "$F" "$HERE/orig/$stamp/"
  rep "$OLD" "$NEW"; python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read())' "$F"
  refresh; echo "применил ($stamp)"
else
  grep -q "kit-patch" "$F" && echo "уже применён" || echo "ВНИМАНИЕ: скрипт автора изменился, строки не найдены — патч не встал"
fi
