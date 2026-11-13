#!/bin/bash
# kit: один перезапуск шелла на всю пачку патчей. Каждый вызов сдвигает общий таймер на 8 с,
# шелл перезапускается один раз, когда последний патч закончил (раньше каждый перезапускал сам).
pgrep -x quickshell >/dev/null || exit 0
systemctl --user stop kit-shell-restart.timer 2>/dev/null || true
systemctl --user reset-failed kit-shell-restart.timer kit-shell-restart.service 2>/dev/null || true
if systemd-run --user --quiet --collect --unit=kit-shell-restart --on-active=8 \
     --timer-property=AccuracySec=1s "$HOME/.local/bin/angelos" restart 2>/dev/null; then
  echo "шелл перезапустится через 8 с (общий таймер)"
else
  "$HOME/.local/bin/angelos" restart >/dev/null 2>&1 && echo "шелл перезапущен"
fi
