#!/usr/bin/env bash
# angelOS pc-kit: what we built on the Mac's VM, put onto a fresh angelOS on the PC (x86_64).
# The VM-only fixes (virgl drawing, x264 recording, the Mac's battery and touchpad bridges,
# the slow scroll, the keep-awake guard, ARM mirrors, Freshgram built from source) stay out.
#
#   ./install.sh                 everything below, asking before angel-niri
#   ./install.sh STEP [STEP…]    only those steps:
#       plugins      the Save point night (meteor, fall, blast, sounds) + the privacy eye + Golden Gate EQ
#       easyeffects  EasyEffects + LV2 plugins, presets «Кайф» and «Концерт», background start
#                    with the tray icon, dark window in angelOS's colours
#       apps         TikTok as an app (Helium), our Pixora icons: TikTok, Helium, Freshgram, Claude,
#                    qThrone, Strata, hwloc, the Dock's buttons; Spotify's icon
#       mac          Golden Gate: the pixel Mac cursor with the halo, «Цвет из обоев», own Pixora icons
#                    and tinted folders without MacTahoe, one set of traffic lights in Settings
#                    and Dock spacing sliders (patches, re-applied after angelOS updates)
#       fixes        Codex's fixes of angelOS bugs (Spotlight blur, bar under the halo, Win+D repeat,
#                    invisible Genie) while the author has none; xdg-terminal-exec for Strata;
#                    speedtest that finds a server through the VPN; X11's default cursor (Steam's top
#                    strip) follows Classic ↔ Golden Gate
#       morph        Classic ↔ Golden Gate ↔ serp switch as an animated transformation with sound
#                    (plugin skin-morph + patch, re-applied after angelOS updates)
#       privacy      privacy mode hides windows on recordings and screenshots too (re-applied
#                    after angelOS updates)
#       windows      windows in desktop mode open where and as big as they were closed
#                    + switching Strip ↔ Desktop (and Classic ↔ Golden Gate) brings each side's
#                    windows back as they were: minimized ones, desks, places (patch)
#       codex        Codex's plugins, each by its own installer: AngelOS Typer (notes on the desktop +
#                    the Typer editor), Room (day and night)
#       niri         angel-niri with Snap / Peek / Win+D, the living pointer and the camera that
#                    follows it, unseen windows suspended, explicit sync for NVIDIA (built from
#                    source, 5–10 min) + «Живой курсор» and «Камера за курсором» in Settings → Cursor
#       satellite    angel-satellite: CS2's 4:3 held and stretched smoothly by niri; unseen X11
#                    windows told they are hidden (they stop drawing)
#       gaming       game mode done to the end: the real owner of an X11 window decides what is a
#                    game (XRes), the angel and the Halo keep quiet over a game; our tools
#                    (celestia-run, celestia-watch, mango-sum…); group games (niri −11)
#       gpu          this PC's RTX 3060 tuning: 120 W, undervolt +200, clock cap 1950 (asks first)
#       serp         the serp skin (Serpantinum's look over angelOS: islands, liquid glass, panels,
#                    its own widget faces), a kit patch re-applied after angelOS updates; switch it
#                    on in Settings → Appearance → Skin
#       walls        our own wallpapers: «Тихая гавань» (a layered scene: hours, smoke, glints,
#                    the window and the lantern on the music) linked into ~/Pictures/Celestia
#
# Every patch of angelOS's files is driven by `kit` (files/../kit/kit.py, linked as ~/.local/bin/kit):
# `kit` shows what is on, `kit doctor` checks the whole setup, one watcher (kit-update.path) puts
# the patches back after an angelOS update.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)/files"
SHELL_DIR="$HOME/.config/quickshell/angelos"
KITHOME="$HOME/.local/share/angelos-kit"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$KITHOME/backup-$STAMP"

say() { printf '\n\033[1;35m== %s\033[0m\n' "$*"; }
ask() { read -r -p "$1 [y/N] " a; [[ "$a" == [yYдД]* ]]; }
keep() {   # a copy of what is about to be replaced, once per run
  local f
  for f in "$@"; do
    [[ -e "$f" ]] || continue
    mkdir -p "$BACKUP$(dirname "$f")"
    cp -a "$f" "$BACKUP$f"
  done
}

[[ $EUID -ne 0 ]] || { echo "запускай от своего пользователя, не от root"; exit 1; }
[[ -d "$SHELL_DIR" ]] || { echo "angelOS не найден ($SHELL_DIR): сначала поставь angelOS его install.sh"; exit 1; }
[[ "$(uname -m)" == x86_64 ]] || echo "внимание: набор собран для x86_64, а тут $(uname -m)"

step_plugins() {
  say "плагины: ночь «Точки сохранения», глазик приватности, эквалайзер Golden Gate"
  local p=~/.config/angelos/plugins
  mkdir -p "$p"
  for name in angelos-night-2004 privacy-eye mac-eq celestia; do
    keep "$p/$name"
    rm -rf "${p:?}/$name"
    cp -a "$KIT/plugins/$name" "$p/"
  done
  # Celestia's face: her moods reach Claude Code through hooks (the pulse hooks of the companion and her own)
  python3 ~/.config/quickshell/angelos/plugins/claude-companion/hooks/install-hooks.py install
  python3 - <<'PY'
import json
from pathlib import Path
f = Path.home() / ".claude/settings.json"
d = json.loads(f.read_text()) if f.exists() else {}
h = d.setdefault("hooks", {}).setdefault("Stop", [])
cmd = str(Path.home() / ".local/bin/celestia-hook")
if not any(cmd in x.get("command", "") for g in h for x in g.get("hooks", [])):
    h.append({"hooks": [{"type": "command", "command": cmd, "timeout": 5}]})
f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
PY
  echo "готово; ночь включится сама (плагин сам покажет обои), настройки — Настройки → Плагины"
}

step_easyeffects() {
  say "EasyEffects"
  sudo pacman -S --needed --noconfirm easyeffects lsp-plugins-lv2 calf mda.lv2
  local out=~/.local/share/easyeffects/output
  mkdir -p "$out" ~/.local/bin ~/.config/autostart
  keep "$out/Кайф.json" "$out/Концерт.json" ~/.config/autostart/easyeffects-service.desktop
  cp "$KIT/easyeffects/presets/"*.json "$out/"
  install -m 0755 "$KIT/easyeffects/easyeffects-start" "$KIT/easyeffects/kde-colors.py" ~/.local/bin/
  printf '%s\n' "[Desktop Entry]" "Type=Application" "Name=Easy Effects" \
    "Exec=$HOME/.local/bin/easyeffects-start" "Icon=com.github.wwmm.easyeffects" \
    "X-GNOME-Autostart-enabled=true" >~/.config/autostart/easyeffects-service.desktop
  python3 -I ~/.local/bin/kde-colors.py easyeffects || true
  echo "готово: со следующего входа EasyEffects стартует в фоне с пресетом «Кайф» и иконкой в трее"
}

# our Pixora icons (Codex) under every name the apps ask for: file:name…
CRAFTS=(photocraft filmcraft)   # ArtCraft apps (AUR), desktop file ai.storyteller.<name>.desktop
ICONS=(tiktok:tiktok tiktok:chrome-www.tiktok.com__-Default helium:helium helium:helium-browser
  freshgram:freshgram freshgram:freshGram freshgram:io.github.snowy-fluffy.freshgram
  claude:claude-desktop claude:com.anthropic.Claude claude:claude qthrone:qthrone qthrone:qThrone
  strata:io.github.lgse.Strata strata:strata hwloc:hwloc
  dockapps:angelos-dock-apps docksettings:angelos-dock-settings dockdownloads:angelos-dock-downloads
  docktrash:angelos-dock-trash docktrashfull:angelos-dock-trash-full)

step_apps() {
  say "TikTok и иконки Pixora"
  local icons=~/.local/share/icons/pixora/scalable/apps hi=~/.local/share/icons/hicolor/scalable/apps apps=~/.local/share/applications
  mkdir -p "$apps" "$hi" "$KITHOME/icons"
  cp "$KIT/icons/"*.svg "$KITHOME/icons/"   # the mac step's patch puts them back from here after updates
  if [[ -d "$icons" ]]; then
    local pair
    for pair in "${ICONS[@]}"; do
      keep "$icons/${pair##*:}.svg"
      rm -f "$icons/${pair##*:}.svg"   # it may be a link into the author's files
      cp "$KIT/icons/${pair%%:*}.svg" "$icons/${pair##*:}.svg"
    done
    for t in pixora pixora-dark; do [[ -d ~/.local/share/icons/$t ]] && gtk-update-icon-cache -f -q ~/.local/share/icons/$t || true; done
  else
    echo "темы Pixora нет ($icons) — иконки пропускаю"
  fi
  # TikTok's own icon also outside Pixora, for any icon theme
  cp "$KIT/icons/tiktok.svg" "$hi/tiktok.svg"
  gtk-update-icon-cache -f -q -t ~/.local/share/icons/hicolor 2>/dev/null || true
  cp "$KIT/apps/chrome-www.tiktok.com__-Default.desktop" "$apps/"
  # a Spotify shortcut whose icon file is missing: the theme's spotify icon
  local f
  for f in "$apps"/spotify*.desktop; do
    [[ -f "$f" ]] || continue
    local icon; icon="$(sed -n 's/^Icon=//p' "$f" | head -1)"
    if [[ "$icon" == /* && ! -e "$icon" ]]; then keep "$f"; sed -i 's|^Icon=.*|Icon=spotify|' "$f"; echo "Spotify: иконка → spotify"; fi
  done
  # qThrone (angelOS installs it, without autostart): starts with the session in the tray
  if [[ -x ~/.local/bin/qthrone ]]; then
    mkdir -p ~/.config/autostart
    printf '%s\n' "[Desktop Entry]" "Type=Application" "Name=qThrone" "Exec=$HOME/.local/bin/qthrone -tray" \
      "X-angelOS-Autostart=true" >~/.config/autostart/angelos-qthrone.desktop
    echo "qThrone: автозапуск в трее"
  fi
  # ArtCraft apps (winit) have no drag-and-drop under Wayland: run them through X11 (angel-satellite)
  local c f
  for c in "${CRAFTS[@]}"; do
    f=ai.storyteller.$c.desktop
    command -v "$c" >/dev/null && [[ -f /usr/share/applications/$f ]] || continue
    keep "$apps/$f"
    sed -e "s|^Exec=$c|Exec=env -u WAYLAND_DISPLAY $c|" /usr/share/applications/$f >"$apps/$f"
    echo "$c: через X11, чтобы работало перетаскивание файлов (вернуть: удалить $apps/$f)"
  done
  update-desktop-database -q "$apps" 2>/dev/null || true
  echo "готово: TikTok в лаунчере (нужен Helium); иконки подхватятся после «angelos restart» или перезахода"
}

step_privacy() {
  say "приватность и на записи экрана"
  kit_patch privacy-capture
}

step_morph() {
  say "морфинг Classic ↔ Golden Gate ↔ serp (анимация + звук)"
  local p=~/.config/angelos/plugins
  mkdir -p "$p"
  keep "$p/skin-morph"
  rm -rf "${p:?}/skin-morph"
  cp -a "$KIT/plugins/skin-morph" "$p/"
  kit_patch skin-morph
}

# the patches live in pc-kit only (KITHOME/patches is a link there); `kit` applies them and the one
# watcher (kit-update.path) puts them back after angelOS updates
kit_setup() {
  mkdir -p "$KITHOME" ~/.local/bin
  if [[ -d "$KITHOME/patches" && ! -L "$KITHOME/patches" ]]; then mv "$KITHOME/patches" "$KITHOME/patches.old-$STAMP"; fi
  ln -sfn "$KIT/patches" "$KITHOME/patches"
  ln -sfn "$KIT/../kit/kit.py" ~/.local/bin/kit
  chmod +x "$KIT/../kit/kit.py" "$KIT/patches/restart-shell.sh" "$KIT"/patches/*/apply.sh 2>/dev/null || true
}
kit_patch() {   # kit_patch NAME…
  kit_setup
  "$KIT/../kit/kit.py" apply "$@" || echo "ВНИМАНИЕ: не всё встало — kit doctor"
}

step_serp() {
  say "скин serp: острова, жидкое стекло, панели, свои виджеты"
  ln -sfn "$KIT/serp-skin" ~/serp-skin            # where it is edited: one copy, here
  kit_patch serp-skin
  # no blur grain under the shell's surfaces (niri's noise is for windows): our own rule in user.kdl
  local u=~/.config/niri/cfg/user.kdl
  if ! grep -q "pc-kit serp-skin" "$u" 2>/dev/null; then
    printf '%s\n' '' '// pc-kit serp-skin: no blur grain under the shell'"'"'s own surfaces (windows keep the noise)' \
      'layer-rule {' '    match namespace="^angelos-"' '    background-effect {' '        noise 0.0' '    }' '}' >>"$u"
  fi
  echo "включить: Настройки → Внешний вид → Скин → serp (или: angelos settingsSkin serp)"
}

step_walls() {
  say "свои обои: «Тихая гавань»"
  mkdir -p ~/Pictures/Celestia
  local w
  for w in "$KIT"/wallpapers/*/; do
    w=${w%/}
    [[ -f "$w/scene.json" ]] || continue
    [[ -e ~/Pictures/Celestia/${w##*/} && ! -L ~/Pictures/Celestia/${w##*/} ]] && keep ~/Pictures/Celestia/"${w##*/}" && rm -rf ~/Pictures/Celestia/"${w##*/}"
    ln -sfn "$w" ~/Pictures/Celestia/"${w##*/}"
  done
  # its music: soft (the window and the lantern swell, a wave from the window), none of the CRT's own
  python3 - "$HOME/.config/angelos/settings.json" "$HOME/Pictures/Celestia/tihaya-gavan" <<'PY'
import json, sys
p, key = sys.argv[1], sys.argv[2]
try:
    d = json.load(open(p))
except OSError:
    sys.exit(0)
pw = d.setdefault("wallpaper", {}).setdefault("perWall", {})
pw.setdefault(key, {"sceneSnare": False, "sceneHats": False, "sceneEdges": False, "sceneBass": False, "sceneBreath": False, "sceneMods": True})
json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
PY
  echo "поставить: Настройки → Обои → «Тихая гавань» (или: angelos wallpaper ~/Pictures/Celestia/tihaya-gavan/reference/neutral.png)"
}

step_mac() {
  say "Golden Gate: мак-курсор, цвет из обоев, свои иконки, один светофор, отступы Дока"
  mkdir -p "$KITHOME/cursor-mac" "$KITHOME/icons"
  rm -rf "$KITHOME/cursor-mac/angelOS-MacPixel"
  cp -a "$KIT/cursor-mac/." "$KITHOME/cursor-mac/"
  cp "$KIT/icons/"*.svg "$KITHOME/icons/"
  kit_patch mac-cursor mac-tint pixora-mac mac-settings-lights dock-spacing
  echo "готово: «Цвет из обоев» — Настройки → Golden Gate → Внешний вид; отступы — там же → Dock"
}

step_fixes() {
  say "исправления багов angelOS от Кодекса"
  kit_patch codex-fixes
  # Strata opens text files in a terminal editor through xdg-terminal-exec, which angelOS doesn't install
  command -v xdg-terminal-exec >/dev/null || sudo pacman -S --needed --noconfirm xdg-terminal-exec
  [[ -f ~/.config/xdg-terminals.list ]] || echo kitty.desktop >~/.config/xdg-terminals.list
  # speedtest through the VPN: the old server list gives only Iran servers and the VPN drops plain http
  # -> own speedtest-cli in ~/.local/bin takes servers from the new API over https
  command -v /usr/bin/speedtest-cli >/dev/null || sudo pacman -S --needed --noconfirm speedtest-cli
  mkdir -p ~/.local/bin; keep ~/.local/bin/speedtest-cli
  install -m 0755 "$KIT/speedtest/speedtest-cli" ~/.local/bin/speedtest-cli
  # X11 apps (Steam) keep Xwayland's start-up cursor where they set none: follow the theme
  command -v xsetroot >/dev/null || sudo pacman -S --needed --noconfirm xorg-xsetroot
  mkdir -p "$KITHOME/x11-cursor" ~/.config/systemd/user
  install -m 0755 "$KIT/x11-cursor/x11-cursor-sync" "$KITHOME/x11-cursor/x11-cursor-sync"
  cp "$KIT/x11-cursor/kit-x11-cursor."{service,path} ~/.config/systemd/user/
  systemctl --user daemon-reload
  systemctl --user enable --now kit-x11-cursor.path
  systemctl --user enable kit-x11-cursor.service
  systemctl --user start kit-x11-cursor.service 2>/dev/null || true
}

step_windows() {
  say "запоминание окон в режиме рабочего стола"
  local d="$KITHOME/window-memory" u=~/.config/systemd/user
  mkdir -p "$d" "$u"
  install -m 0755 "$KIT/window-memory/window-memory.py" "$d/window-memory.py"
  printf '%s\n' "[Unit]" "Description=angelOS: окна в DE-режиме открываются там же и того же размера, где их закрыли" \
    "After=niri.service" "PartOf=graphical-session.target" "" \
    "[Service]" "ExecStart=$d/window-memory.py" "Restart=on-failure" "RestartSec=3" "" \
    "[Install]" "WantedBy=graphical-session.target" >"$u/window-memory.service"
  systemctl --user daemon-reload
  systemctl --user enable window-memory.service
  systemctl --user restart window-memory.service 2>/dev/null || echo "заработает со следующего входа"
  # Strip ↔ Desktop (and Classic's Strip ↔ Golden Gate with step morph) remembers each side's windows
  kit_patch stack-memory
}

step_codex() {
  say "плагины Кодекса: Typer, Комната"
  local c="$KIT/codex-plugins"
  [[ -f ~/.config/angelos/settings.json ]] || { echo "нет ~/.config/angelos/settings.json — сначала войди в angelOS, потом повтори шаг codex"; return; }
  # Typer is a GTK 4 editor; its installer also makes it the default for text and Markdown
  sudo pacman -S --needed --noconfirm python-gobject gtk4 libadwaita gtksourceview5 librsvg
  python3 -I "$c/AngelOS-Typer/install.py" || echo "Typer: установщик споткнулся (см. выше)"
  python3 -I "$c/AngelOS-Room/install.py" || echo "Комната: установщик споткнулся (см. выше)"
  qs -c angelos ipc call angelos plugins >/dev/null 2>&1 || true
  echo "готово: обои «Комната» — в выборе обоев; заметки — Typer в лаунчере"
}

step_niri() {
  say "angel-niri со Snap / Peek / Win+D, живым курсором и камерой"
  if [[ "${ALL:-0}" == 1 ]] && ! ask "Собрать angel-niri с патчами (5–10 минут)?"; then return; fi
  bash "$KIT/angel-niri/build-niri.sh"
  kit_patch cursor-motion
  echo "живой курсор и камера — со следующего входа; настройки: Classic → Курсор, Golden Gate → Курсор; камера — Super+Ctrl+Shift+U"
}

step_satellite() {
  say "angel-satellite: 4:3 без лесенки, скрытые X11-окна не рисуют"
  bash "$KIT/angel-satellite/build-satellite.sh"
}

step_gaming() {
  say "игровой режим до конца + наши инструменты"
  kit_patch game-detect angel-game-quiet halo-game-sleep
  python3 -c 'import Xlib' 2>/dev/null || sudo pacman -S --needed --noconfirm python-xlib   # game-detect asks X who owns a window
  local f
  for f in "$KIT"/tools/*; do ln -sfn "$f" ~/.local/bin/"$(basename "$f")"; done
  mkdir -p ~/.config/celestia-run
  for f in "$KIT"/celestia-run/*.conf; do ln -sfn "$f" ~/.config/celestia-run/"$(basename "$f")"; done
  install -m 0755 "$KIT/angel-satellite/celestia-hold" ~/.local/bin/celestia-hold
  # niri −11 and the focused game's boost need the nice limit the games group has (limits.conf)
  id -nG | grep -qw games || { sudo gpasswd -a "$USER" games && echo "группа games: со следующей перезагрузки"; }
  echo "в Steam: параметры запуска «$HOME/.local/bin/celestia-run %command%»; CS2: Reflex выкл (замерено хуже)"
}

step_gpu() {
  say "RTX 3060 этого компа: 120 Вт, андервольт +200, потолок 1950 МГц"
  if ! ask "Ставить настройки видеокарты (подобраны под эту RTX 3060; на другой карте не нужно)?"; then return; fi
  sudo install -D -m 0755 "$KIT/system/gpu-offset.py" /usr/local/lib/celestia/gpu-offset.py
  sudo install -m 0644 "$KIT/system/nvidia-power-limit.service" "$KIT/system/nvidia-gpu-offset.service" /etc/systemd/system/
  [[ -f /usr/local/lib/angelos/gpu-clocks && ! -f /usr/local/lib/angelos/gpu-clocks.angelos-orig ]] && \
    sudo cp -a /usr/local/lib/angelos/gpu-clocks /usr/local/lib/angelos/gpu-clocks.angelos-orig
  sudo install -D -m 0755 "$KIT/system/gpu-clocks" /usr/local/lib/angelos/gpu-clocks
  sudo systemctl daemon-reload
  sudo systemctl enable --now nvidia-power-limit.service nvidia-gpu-offset.service
  # fans 50 % while warm; EasyEffects checked after sleep (celestia-sleep)
  sudo install -D -m 0755 "$KIT/system/gpu-fan-curve.py" /usr/local/lib/celestia/gpu-fan-curve.py
  sudo install -D -m 0755 "$KIT/system/celestia-sleep" /usr/local/lib/celestia/celestia-sleep
  sudo install -m 0644 "$KIT/system/nvidia-fan-curve.service" "$KIT/system/celestia-wake.service" /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now nvidia-fan-curve.service
  sudo systemctl enable celestia-wake.service
  # Bluetooth stays off until asked: its USB adapter comes back at every wake, and BlueZ powered it on behind the shell
  sudo sed -i 's/^#AutoEnable=true$/AutoEnable=false/' /etc/bluetooth/main.conf
  echo "в Настройках → Игры «Видеокарта на полной частоте» держи выключенной: потолок держит наш gpu-clocks"
}

steps=("$@")
if [[ ${#steps[@]} -eq 0 ]]; then ALL=1; steps=(plugins easyeffects apps mac morph serp walls privacy fixes codex windows niri satellite gaming gpu); fi
for s in "${steps[@]}"; do
  case "$s" in
    plugins|easyeffects|apps|mac|morph|serp|walls|privacy|fixes|codex|windows|niri|satellite|gaming|gpu) "step_$s" ;;
    *) echo "нет шага «$s»"; exit 1 ;;
  esac
done

kit_setup
"$KIT/../kit/kit.py" install-watcher
say "всё"
"$KIT/../kit/kit.py" doctor || true
[[ -d "$BACKUP" ]] && echo "заменённое сохранено в $BACKUP"
echo "Перезапусти оболочку (angelos restart) или перезайди; angel-niri и автозапуски — со следующего входа."
