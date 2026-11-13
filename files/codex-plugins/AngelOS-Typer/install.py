#!/usr/bin/env python3
"""Install for the current user. Keep upstream angelOS files untouched."""
from pathlib import Path
import argparse
import datetime
import json
import os
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parent
HOME = Path.home()


def install_icons(backup):
    source = SOURCE / "assets/local.angelos.Typer.svg"
    icon_home = HOME / ".local/share/icons"
    # Keep a hicolor fallback and add only our own icon to installed Pixora layers.
    themes = ["hicolor", "pixora", "pixora-dark", "angelos-folders-a", "angelos-folders-b"]
    for name in themes:
        theme = icon_home / name
        if name != "hicolor" and not theme.is_dir():
            continue
        target = theme / "scalable/apps/local.angelos.Typer.svg"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            saved = backup / "icons" / name
            saved.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved / target.name)
        shutil.copy2(source, target)
        if shutil.which("gtk-update-icon-cache"):
            subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(theme)], capture_output=True)
    if shutil.which("rsvg-convert"):
        for size in [16, 32, 48, 64, 128, 256]:
            target = icon_home / "hicolor" / f"{size}x{size}/apps/local.angelos.Typer.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(target), str(source)], check=True)
        if shutil.which("gtk-update-icon-cache"):
            subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(icon_home / "hicolor")], capture_output=True)


def install_plugin(backup):
    plugins = HOME / ".config/angelos/plugins"
    plugins.mkdir(parents=True, exist_ok=True)
    destination = plugins / "angelos-typer"
    if destination.exists():
        destination.rename(backup / "previous-plugin")
    with tempfile.TemporaryDirectory(prefix=".typer-stage-", dir=plugins.parent) as temporary:
        staged = Path(temporary) / "angelos-typer"
        shutil.copytree(SOURCE / "plugin", staged)
        staged.rename(destination)
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-default", action="store_true")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--plugin-only", action="store_true")
    scope.add_argument("--app-only", action="store_true", help="Update the editor without replacing the notes plugin")
    args = parser.parse_args()
    if args.plugin_only:
        backup = HOME / ".local/state/angelos-typer/plugin-backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup.mkdir(parents=True, exist_ok=False)
        print("Plugin:", install_plugin(backup))
        desktop = HOME / ".local/share/applications/local.angelos.Typer.desktop"
        if desktop.exists():
            shutil.copy2(desktop, backup / "Typer.desktop")
            shutil.copy2(SOURCE / "assets/local.angelos.Typer.desktop", desktop)
            if shutil.which("update-desktop-database"):
                subprocess.run(["update-desktop-database", str(desktop.parent)], check=True)
        installed_asset = HOME / ".local/share/angelos-typer/app/assets/local.angelos.Typer.desktop"
        if installed_asset.exists():
            shutil.copy2(SOURCE / "assets/local.angelos.Typer.desktop", installed_asset)
        install_icons(backup)
        installed_icon = HOME / ".local/share/angelos-typer/app/assets/local.angelos.Typer.svg"
        if installed_icon.exists():
            shutil.copy2(SOURCE / "assets/local.angelos.Typer.svg", installed_icon)
        print("Backup:", backup)
        return
    import gi
    for namespace, version in [("Gtk", "4.0"), ("Adw", "1"), ("GtkSource", "5")]:
        gi.require_version(namespace, version)
    data = HOME / ".local/share/angelos-typer"
    data.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = HOME / ".local/state/angelos-typer/install-backups" / stamp
    backup.mkdir(parents=True, exist_ok=False)
    for original, name in [
        (HOME / ".config/mimeapps.list", "config-mimeapps.list"),
        (HOME / ".local/share/applications/mimeapps.list", "data-mimeapps.list"),
        (HOME / ".local/share/applications/local.angelos.Typer.desktop", "Typer.desktop"),
        (HOME / ".local/bin/angelos-typer", "angelos-typer-launcher"),
    ]:
        if original.exists():
            shutil.copy2(original, backup / name)
    defaults = {}
    for mime in ["text/plain", "text/markdown", "text/x-markdown"]:
        result = subprocess.run(["xdg-mime", "query", "default", mime], capture_output=True, text=True)
        defaults[mime] = result.stdout.strip()
    (backup / "previous-defaults.json").write_text(json.dumps(defaults, indent=2))
    state = HOME / ".local/state/angelos-typer"
    for name in ["drafts", "session.json", "settings.json"]:
        original = state / name
        if original.is_dir():
            shutil.copytree(original, backup / name)
        elif original.is_file():
            shutil.copy2(original, backup / name)
    with tempfile.TemporaryDirectory(prefix=".install-", dir=data) as temporary:
        staged = Path(temporary) / "app"
        staged.mkdir()
        for name in ["angelos_typer", "assets"]:
            shutil.copytree(SOURCE / name, staged / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if (data / "app").exists():
            (data / "app").rename(backup / "previous-app")
        staged.rename(data / "app")
    launcher = HOME / ".local/bin/angelos-typer"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text('#!/bin/sh\nexport PYTHONPATH="$HOME/.local/share/angelos-typer/app${PYTHONPATH:+:$PYTHONPATH}"\nexec /usr/bin/python3 -m angelos_typer "$@"\n')
    launcher.chmod(0o755)
    applications = HOME / ".local/share/applications"
    applications.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE / "assets/local.angelos.Typer.desktop", applications)
    install_icons(backup)
    destination = None if args.app_only else install_plugin(backup)
    if shutil.which("update-desktop-database"):
        subprocess.run(["update-desktop-database", str(applications)], check=True)
    if not args.no_default:
        for mime in defaults:
            subprocess.run(["xdg-mime", "default", "local.angelos.Typer.desktop", mime], check=True)
    print("Installed AngelOS Typer")
    print("Launcher:", launcher)
    if destination:
        print("Plugin:", destination)
    print("Backup:", backup)


if __name__ == "__main__":
    main()
