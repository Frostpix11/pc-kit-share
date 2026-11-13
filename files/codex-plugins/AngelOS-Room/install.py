#!/usr/bin/env python3
"""Install the user plugin without modifying angelOS or the author's wallpaper pack."""
from datetime import datetime
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
PLUGIN = HOME / ".config/angelos/plugins/angelos-room"
WALLS = HOME / "Pictures/AngelOS-Room"


def main():
    for variant in ("day", "night"):
        link = WALLS / variant
        expected = PLUGIN / "scenes" / variant
        if link.is_symlink() and link.readlink() == expected:
            continue
        if link.exists() or link.is_symlink():
            raise SystemExit(f"Refusing to replace existing wallpaper directory: {link}")
    if not (ROOT / "plugin/scenes/night/scene.json").is_file():
        raise SystemExit("Run build_assets.py first")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = HOME / ".local/state/angelos-room/backups" / stamp
    backup.mkdir(parents=True, exist_ok=False)
    settings = HOME / ".config/angelos/settings.json"
    if settings.is_file():
        shutil.copy2(settings, backup / "settings-before.json")
    if PLUGIN.exists():
        shutil.copytree(PLUGIN, backup / "plugin")
    PLUGIN.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "plugin", PLUGIN, dirs_exist_ok=True)
    WALLS.mkdir(parents=True, exist_ok=True)
    for variant in ("day", "night"):
        link = WALLS / variant
        if not link.is_symlink():
            link.symlink_to(PLUGIN / "scenes" / variant, target_is_directory=True)
    print(f"Installed: {PLUGIN}\nWallpaper links: {WALLS}\nBackup: {backup}")
    print("Load with: qs -c angelos ipc call angelos plugins")


if __name__ == "__main__":
    main()
