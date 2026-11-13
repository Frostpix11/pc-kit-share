"""Native GTK application and angelOS integration."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import re
import sys
import time
import signal
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk, Adw, Gdk, Gio, GLib, GtkSource

from .core import Document, Storage, ExternalChangeError, TEXT_SUFFIXES, atomic_write, format_text, text_files
from .widgets import DocumentPage, FolderTree, label, button, clear
from . import preview, spelling
from . import __version__

APP_ID = "local.angelos.Typer"
FORMATS = [("Жирный", "bold"), ("Курсив", "italic"), ("Зачёркнутый", "strike"), ("Код", "code"), ("Ссылка", "link"), ("Заголовок 1", "h1"), ("Заголовок 2", "h2"), ("Заголовок 3", "h3"), ("Список", "bullet"), ("Список дел", "task"), ("Цитата", "quote")]


class Typer(Adw.Application):
    def __init__(self, state_directory=None, testing=False):
        flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        if testing:
            flags |= Gio.ApplicationFlags.NON_UNIQUE
        super().__init__(application_id=APP_ID, flags=flags)
        state_home = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state")))
        self.storage = Storage(state_directory or state_home / "angelos-typer")
        self.settings = self.storage.read_json("settings.json", {})
        self.pages = {}
        self.preview_page = None
        self.win = None
        self.folder = None
        self.folder_monitor = None
        self.focus_mode = False
        self.allow_close = False
        self.closing_window = False
        self.stopping = False
        self.draft_timer = 0
        self.spell_timer = 0
        self.refresh_timer = 0
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="typer")
        self.connect("shutdown", self.shutdown_app)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.terminate)

    def do_command_line(self, command):
        args = list(command.get_arguments())[1:]
        if "--version" in args:
            command.print_literal("AngelOS Typer " + __version__ + "\n")
            return 0
        quick = "--quick-note" in args
        paths = [arg for arg in args if not arg.startswith("--")]
        self.activate()
        for item in paths:
            file = command.create_file_for_arg(item)
            path = file.get_path()
            if path:
                self.open_path(Path(path))
            else:
                self.error("Поддерживаются локальные файлы", item)
        if quick:
            self.new_document(title="Быстрая заметка.md")
        self.win.present()
        return 0

    def do_activate(self):
        if self.win:
            self.win.present()
            return
        self.build_window()
        self.restore_session()
        self.win.present()

    def build_window(self):
        Gtk.Window.set_default_icon_name(APP_ID)
        self.win = Gtk.ApplicationWindow(application=self, default_width=1180, default_height=800)
        self.win.set_title("AngelOS Typer")
        self.win.set_size_request(760, 540)
        self.win.connect("close-request", self.close_window)
        self.toasts = Adw.ToastOverlay()
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toasts.set_child(outer)
        self.win.set_child(self.toasts)
        self.win.add_css_class("typer-window")
        header = Gtk.Box(spacing=6)
        header.add_css_class("typer-toolbar")
        header.append(button("", "local.angelos.Typer", lambda _: self.toggle_sidebar(), "Дерево файлов · Ctrl+B"))
        header.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        header.append(button("Новый", "text-x-generic", lambda _: self.new_document(), "Новый текст · Ctrl+N"))
        header.append(button("Открыть", "folder-document", lambda _: self.choose_file(), "Открыть файл · Ctrl+O"))
        header.append(button("Папка", "folder", lambda _: self.choose_folder(), "Открыть папку · Ctrl+Shift+O"))
        header.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        header.append(button("Сохранить", "document-save-symbolic", lambda _: self.save_current(), "Сохранить · Ctrl+S"))
        header.append(Gtk.Box(hexpand=True))
        header.append(button("", "preferences-system-search", lambda _: self.show_find(), "Найти в тексте · Ctrl+F"))
        menu = Gio.Menu()
        for title, name, callback in [
            ("Открыть папку…", "folder", lambda *_: self.choose_folder()),
            ("Перейти к файлу…", "quick", lambda *_: self.search_dialog(False)),
            ("Найти в папке…", "folder-search", lambda *_: self.search_dialog(True)),
            ("Сохранить как…", "save-as", lambda *_: self.save_current(True)),
            ("Закрепить в избранном", "favorite", lambda *_: self.favorite()),
            ("Только текст", "focus", lambda *_: self.toggle_focus()),
            ("Настройки", "preferences", lambda *_: self.preferences()),
            ("О Typer", "about", lambda *_: self.about()),
        ]:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)
            menu.append(title, "app." + name)
        for title, kind in FORMATS:
            action = Gio.SimpleAction.new("format-" + kind, None)
            action.connect("activate", lambda *_, k=kind: self.format_selection(k))
            self.win.add_action(action)
        action = Gio.SimpleAction.new("spell-replace", GLib.VariantType.new("(iis)"))
        action.connect("activate", self.replace_spelling)
        self.win.add_action(action)
        header.append(Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu, tooltip_text="Действия"))
        outer.append(header)

        self.workspace = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, wide_handle=True, vexpand=True)
        self.workspace.set_position(260)
        self.workspace.set_shrink_start_child(False)
        self.workspace.set_shrink_end_child(False)
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, width_request=215)
        self.sidebar.add_css_class("typer-sidebar")
        top = Gtk.Box(spacing=6, margin_start=10, margin_end=10, margin_top=10, margin_bottom=4)
        self.folder_label = Gtk.Label(label="Файлы", xalign=0, hexpand=True, ellipsize=3)
        top.append(button("", "folder", lambda _: self.choose_folder(), "Открыть папку"))
        top.append(self.folder_label)
        top.append(button("", "preferences-system-search", lambda _: self.search_dialog(True), "Поиск по папке"))
        self.sidebar.append(top)
        self.side_scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        side_body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.favorites_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.recent_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.tree_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        side_body.append(self.favorites_box)
        side_body.append(self.recent_box)
        self.file_heading = self.section("ФАЙЛЫ ПАПКИ")
        side_body.append(self.file_heading)
        side_body.append(self.tree_box)
        self.side_scroll.set_child(side_body)
        self.sidebar.append(self.side_scroll)
        sidebar_actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, margin_start=8, margin_end=8, margin_bottom=8)
        self.clear_tree_button = button("Очистить дерево", "edit-clear-symbolic", lambda _: self.clear_folders(), "Убрать текущую и недавние папки из дерева. Файлы останутся на диске.")
        sidebar_actions.append(self.clear_tree_button)
        sidebar_actions.append(button("Быстрая заметка", "text-x-generic", lambda _: self.new_document(title="Быстрая заметка.md")))
        self.sidebar.append(sidebar_actions)
        self.tree = FolderTree(self.tree_box, self.open_file, self.error)
        self.workspace.set_start_child(self.sidebar)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.tabs = Adw.TabView(vexpand=True)
        self.tabs.connect("notify::selected-page", lambda *_: self.refresh())
        self.tabs.connect("close-page", self.close_page)
        self.tabs.connect("page-detached", self.detached)
        self.tabbar = Adw.TabBar(view=self.tabs, autohide=False, expand_tabs=False)
        self.tabbar.add_css_class("typer-tabs")
        main.append(self.tabbar)
        toolbar = Gtk.Box(spacing=6)
        toolbar.add_css_class("typer-location")
        toolbar.append(Gtk.Image.new_from_icon_name("text-x-generic"))
        self.path_label = Gtk.Label(xalign=0, hexpand=True, ellipsize=3)
        self.path_label.add_css_class("dim-label")
        toolbar.append(self.path_label)
        self.preview_button = Gtk.ToggleButton(label="Просмотр", tooltip_text="Текст / Markdown-просмотр · Ctrl+Shift+M")
        self.preview_button.connect("toggled", lambda *_: self.refresh())
        toolbar.append(self.preview_button)
        self.outline_button = Gtk.ToggleButton(label="Оглавление")
        self.outline_button.connect("toggled", lambda b: self.outline.set_visible(b.get_active() and not self.focus_mode))
        toolbar.append(self.outline_button)
        self.focus_button = button("Только текст", "view-fullscreen-symbolic", lambda _: self.toggle_focus(), "Режим сосредоточения · F11")
        toolbar.append(self.focus_button)
        main.append(toolbar)

        self.search_reveal = Gtk.Revealer()
        searches = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin_start=18, margin_end=18, margin_bottom=10)
        find_row = Gtk.Box(spacing=8)
        self.find = Gtk.SearchEntry(hexpand=True, placeholder_text="Найти в этом тексте…")
        self.find.connect("search-changed", lambda *_: self.find_next(True))
        self.find.connect("activate", lambda *_: self.find_next())
        find_row.append(self.find)
        find_row.append(button("Далее", None, lambda _: self.find_next()))
        find_row.append(button("", "window-close-symbolic", lambda _: self.search_reveal.set_reveal_child(False), "Закрыть поиск"))
        searches.append(find_row)
        replace_row = Gtk.Box(spacing=8)
        self.replacement = Gtk.Entry(hexpand=True, placeholder_text="Заменить на…")
        replace_row.append(self.replacement)
        replace_row.append(button("Заменить", None, lambda _: self.replace_text(False)))
        replace_row.append(button("Все", None, lambda _: self.replace_text(True)))
        searches.append(replace_row)
        self.search_reveal.set_child(searches)
        main.append(self.search_reveal)
        main.append(Gtk.Separator())
        area = Gtk.Box(hexpand=True, vexpand=True)
        area.append(self.tabs)
        self.outline = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7, width_request=170, margin_start=12, margin_end=12, margin_top=18, visible=False)
        self.outline_scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, min_content_width=180)
        self.outline_scroll.set_child(self.outline)
        self.outline_scroll.set_visible(False)
        self.outline.connect("notify::visible", lambda w, _: self.outline_scroll.set_visible(w.get_visible()))
        area.append(self.outline_scroll)
        main.append(area)
        self.workspace.set_end_child(main)
        outer.append(self.workspace)
        outer.append(Gtk.Separator())
        status = Gtk.Box(spacing=16, margin_start=18, margin_end=18, margin_top=8, margin_bottom=8)
        self.state_label = Gtk.Label(xalign=0, hexpand=True)
        self.state_label.add_css_class("dim-label")
        self.count = Gtk.Label()
        status.add_css_class("typer-status")
        status.append(self.state_label)
        status.append(self.count)
        outer.append(status)
        keys = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.key)
        self.win.add_controller(keys)
        self.install_css()
        self.refresh_sidebar()

    def section(self, text):
        widget = label(text, "caption-heading")
        widget.set_margin_start(16)
        widget.set_margin_top(15)
        widget.set_margin_bottom(5)
        return widget

    def install_css(self):
        self.css = Gtk.CssProvider()
        self.apply_font()
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.theme_monitor = None
        palette = Path.home() / ".cache/angelos/palette.json"
        if palette.exists():
            try:
                self.theme_monitor = Gio.File.new_for_path(str(palette.parent)).monitor_directory(Gio.FileMonitorFlags.NONE, None)
                self.theme_monitor.connect("changed", lambda m, f, o, e: self.apply_font() if f.get_basename() == "palette.json" else None)
            except GLib.Error:
                pass

    def apply_font(self):
        import json
        font = None
        data = {}
        try:
            data = json.loads((Path.home() / ".cache/angelos/palette.json").read_text())
            font = data.get("fontBody") if not data.get("skin") and not data.get("hell") else None
        except (OSError, ValueError):
            pass
        size = int(self.settings.get("font_size", 16))
        family = ('font-family: "' + font.replace('"', '') + '";') if font else ""
        colors = data.get("hell") or data
        background = colors.get("sunken", data.get("macContent", "#ffffff"))
        foreground = colors.get("text", data.get("macText", "#202020"))
        if data.get("skin") and not data.get("hell"):
            background = data.get("macContent", background)
            foreground = data.get("macText", foreground)
        face = colors.get("face", data.get("macSurface", background))
        alternate = colors.get("faceAlt", face)
        edge = colors.get("decorEdge", data.get("decorEdge", "#465054"))
        accent = colors.get("accent", "#87b0b3")
        dim = colors.get("textDim", foreground)
        self.css.load_from_data((f"""
            .typer-window {{ background: {background}; color: {foreground}; }}
            .typer-window > box, .typer-window .typer-sidebar {{ background: {face}; }}
            .typer-window button {{ border-radius: 2px; min-height: 26px; padding: 3px 8px; }}
            .typer-window button:not(:hover):not(:checked) {{ background: transparent; box-shadow: none; }}
            .typer-window button:hover {{ background: {alternate}; }}
            .typer-window button:checked {{ background: {accent}; color: {background}; }}
            .typer-toolbar {{ background: {face}; padding: 6px 10px; border-bottom: 1px solid {edge}; }}
            .typer-sidebar {{ border-right: 1px solid {edge}; }}
            .typer-sidebar button {{ padding: 3px 6px; }}
            .typer-sidebar expander {{ margin-top: 2px; margin-bottom: 2px; }}
            .typer-sidebar .caption-heading {{ color: {dim}; font-size: 11px; letter-spacing: 1px; }}
            .typer-location {{ background: {face}; padding: 5px 12px; border-bottom: 1px solid {edge}; }}
            .typer-tabs tabbar tabbox {{ background: {face}; padding: 0; }}
            .typer-tabs tab {{ border-radius: 0; box-shadow: none; border-right: 1px solid {edge}; }}
            .typer-tabs tab:selected {{ background: {background}; border-bottom: 2px solid {accent}; }}
            .typer-status {{ font-size: 12px; color: {dim}; }}
            .typer-editor {{ {family} font-size: {size}px; }}
        """).encode())
        try:
            rgb = [int(background[index:index+2], 16) for index in (1, 3, 5)]
            dark = sum(rgb) < 384
        except (ValueError, IndexError):
            dark = False
        element = ET.Element("style-scheme", {"id": "angelos-typer-palette", "name": "angelOS", "version": "1.0", "parent-scheme": "Adwaita-dark" if dark else "Adwaita"})
        for name, attributes in [
            ("text", {"foreground": foreground, "background": background}),
            ("selection", {"foreground": colors.get("selectText", background), "background": colors.get("accent", "#87b0b3")}),
            ("cursor", {"foreground": foreground}),
            ("line-numbers", {"foreground": colors.get("textDim", foreground), "background": background}),
            ("def:comment", {"foreground": colors.get("textDim", "#808080")}),
            ("def:heading", {"foreground": colors.get("accent", foreground), "bold": "true"}),
        ]:
            ET.SubElement(element, "style", dict(name=name, **attributes))
        theme_dir = self.storage.directory / "themes"
        theme_dir.mkdir(exist_ok=True)
        atomic_write(theme_dir / "angelos.xml", ET.tostring(element, encoding="utf-8", xml_declaration=True))
        manager = GtkSource.StyleSchemeManager()
        manager.append_search_path(str(theme_dir))
        manager.force_rescan()
        self.scheme_manager = manager
        self.scheme = manager.get_scheme("angelos-typer-palette")
        for page in self.pages.values():
            page.buffer.set_style_scheme(self.scheme)

    def current(self):
        return self.pages.get(self.tabs.get_selected_page())

    def open_path(self, path):
        if path.is_dir():
            self.set_folder(path)
        else:
            self.open_file(path, True)

    def set_folder(self, path):
        path = path.expanduser().resolve()
        if not path.is_dir():
            self.error("Не удалось открыть папку", str(path))
            return
        self.folder = path
        self.folder_label.set_text(path.name or str(path))
        self.folder_label.set_tooltip_text(str(path))
        self.tree.load(path)
        self.settings["folder"] = str(path)
        self.settings["recent_folders"] = [str(path)] + [p for p in self.settings.get("recent_folders", []) if p != str(path)][:4]
        if self.folder_monitor:
            self.folder_monitor.cancel()
        try:
            self.folder_monitor = Gio.File.new_for_path(str(path)).monitor_directory(Gio.FileMonitorFlags.NONE, None)
            self.folder_monitor.connect("changed", lambda *_: self.queue_tree_refresh())
        except GLib.Error:
            self.folder_monitor = None
        self.refresh_sidebar()
        self.queue_checkpoint()

    def clear_folders(self):
        if self.refresh_timer:
            GLib.source_remove(self.refresh_timer)
            self.refresh_timer = 0
        if self.folder_monitor:
            self.folder_monitor.cancel()
            self.folder_monitor = None
        self.tree.reset()
        self.folder = None
        self.settings.pop("folder", None)
        self.settings["recent_folders"] = []
        self.folder_label.set_text("Файлы")
        self.folder_label.set_tooltip_text(None)
        self.refresh_sidebar()
        if self.draft_timer:
            GLib.source_remove(self.draft_timer)
            self.draft_timer = 0
        self.persist()
        self.toast("Дерево очищено. Файлы сохранены на диске.")

    def queue_tree_refresh(self):
        if self.refresh_timer:
            GLib.source_remove(self.refresh_timer)
        def run():
            self.refresh_timer = 0
            if self.folder:
                self.tree.load(self.folder)
            return False
        self.refresh_timer = GLib.timeout_add(700, run)

    def refresh_sidebar(self):
        self.clear_tree_button.set_sensitive(bool(self.folder or self.settings.get("recent_folders")))
        clear(self.favorites_box)
        favorites = self.settings.get("favorites", [])
        if favorites:
            self.favorites_box.append(self.section("ИЗБРАННОЕ"))
            for value in favorites:
                path = Path(value)
                if path.is_file():
                    self.favorites_box.append(self.tree.file_button(path, True))
                elif path.is_dir():
                    self.favorites_box.append(button(path.name, "folder", lambda _, p=path: self.set_folder(p), str(path)))
        clear(self.recent_box)
        recent = [Path(p) for p in self.settings.get("recent_folders", []) if Path(p).is_dir() and Path(p) != self.folder]
        if recent:
            self.recent_box.append(self.section("НЕДАВНИЕ ПАПКИ"))
            for path in recent:
                b = button(path.name, "folder", lambda _, p=path: self.set_folder(p), str(path))
                b.add_css_class("flat")
                self.recent_box.append(b)
        if not self.folder:
            clear(self.tree_box)
            self.tree_box.append(button("Открыть папку…", "folder", lambda _: self.choose_folder()))

    def favorite(self, folder=False):
        page = self.current()
        path = self.folder if folder else page.document.path if page else None
        if not path:
            self.toast("Сначала сохрани документ или открой папку.")
            return
        values = self.settings.setdefault("favorites", [])
        value = str(path)
        if value in values:
            values.remove(value)
            self.toast("Убрано из избранного")
        else:
            values.append(value)
            self.toast("Добавлено в избранное")
        self.refresh_sidebar()
        self.queue_checkpoint()

    def open_file(self, path, permanent=False):
        try:
            path = Path(path).expanduser().resolve()
            for page in self.pages.values():
                if page.document.path == path:
                    self.tabs.set_selected_page(page.tab)
                    if permanent:
                        self.pin(page)
                    return page
            document = Document.load(path)
        except (OSError, ValueError, UnicodeError) as error:
            self.error("Не удалось открыть текст", str(error))
            return None
        return self.add_document(document, permanent)

    def add_document(self, document, permanent=True):
        if not permanent and self.preview_page in self.pages:
            previous = self.pages[self.preview_page]
            if not previous.document.dirty:
                self.tabs.close_page(self.preview_page)
        page = DocumentPage(document)
        page.buffer.set_style_scheme(self.scheme)
        tab = self.tabs.append(page.stack)
        page.tab = tab
        page.permanent = permanent
        self.pages[tab] = page
        tab.set_title(document.title)
        tab.set_tooltip(str(document.path or document.title))
        if not permanent:
            self.preview_page = tab
            tab.set_indicator_icon(Gio.ThemedIcon.new("view-reveal-symbolic"))
            tab.set_indicator_tooltip("Временный просмотр · двойной клик или редактирование оставляет вкладку")
        page.buffer.connect("changed", lambda *_: self.changed(page))
        page.buffer.connect("notify::cursor-position", lambda *_: self.update_counts())
        self.context_menu(page)
        context = Gtk.GestureClick(button=3, propagation_phase=Gtk.PropagationPhase.CAPTURE)
        context.connect("pressed", lambda _, n, x, y: self.context_at(page, x, y))
        page.editor.add_controller(context)
        swipe = Gtk.GestureSwipe(touch_only=True)
        swipe.connect("swipe", self.swipe)
        page.editor.add_controller(swipe)
        scrolling = Gtk.EventControllerScroll(flags=Gtk.EventControllerScrollFlags.BOTH_AXES, propagation_phase=Gtk.PropagationPhase.CAPTURE)
        scrolling.connect("scroll", self.scroll_tabs)
        page.editor.add_controller(scrolling)
        self.tabs.set_selected_page(tab)
        if document.cursor:
            page.buffer.place_cursor(page.buffer.get_iter_at_offset(min(document.cursor, page.buffer.get_char_count())))
        self.refresh()
        self.queue_checkpoint()
        self.queue_spell(page)
        return page

    def pin(self, page):
        page.permanent = True
        page.tab.set_indicator_icon(None)
        if self.preview_page == page.tab:
            self.preview_page = None

    def new_document(self, text="", title="Новый текст.md"):
        document = Document(text=text, title=title)
        page = self.add_document(document, True)
        page.editor.grab_focus()
        return page

    def changed(self, page):
        if page.tab not in self.pages:
            return
        page.synchronize()
        self.pin(page)
        page.tab.set_title(page.document.title + (" •" if page.document.dirty else ""))
        self.queue_checkpoint()
        self.queue_spell(page)
        if self.current() == page:
            self.refresh()

    def refresh(self):
        if not hasattr(self, "path_label"):
            return
        page = self.current()
        if not page:
            self.path_label.set_text("Новый текст или открой файл")
            self.state_label.set_text("Ctrl+N — новый · Ctrl+O — открыть")
            self.count.set_text("")
            clear(self.outline)
            return
        doc = page.document
        self.path_label.set_text(str(doc.path or doc.title))
        self.path_label.set_tooltip_text(str(doc.path or doc.title))
        self.win.set_title(doc.title + (" •" if doc.dirty else "") + " — AngelOS Typer")
        self.state_label.set_text(("Не сохранено · черновик защищён" if doc.dirty else "Сохранено" if doc.path else "Новый документ") + " · " + doc.encoding.upper())
        self.preview_button.set_sensitive(doc.markdown)
        show = self.preview_button.get_active() and doc.markdown
        page.stack.set_visible_child_name("preview" if show else "edit")
        if show:
            preview.render(page.preview, page.text(), lambda uri: self.open_link(page, uri))
        clear(self.outline)
        self.outline.append(label("ОГЛАВЛЕНИЕ", "caption-heading"))
        found = False
        for number, line in enumerate(page.text().splitlines()):
            if re.match(r"^#{1,6}\s", line):
                found = True
                title = line.lstrip("# ")
                item = Gtk.Button()
                item.set_child(label(title))
                item.add_css_class("flat")
                item.connect("clicked", lambda _, n=number: self.jump_line(n))
                self.outline.append(item)
        if not found:
            self.outline.append(label("В этом тексте нет заголовков.", "dim-label"))
        self.update_counts()

    def update_counts(self):
        page = self.current()
        if not page:
            return
        text = page.text()
        cursor = page.buffer.get_iter_at_mark(page.buffer.get_insert())
        self.count.set_text(f"{len(text.split())} слов · {len(text)} знаков · {cursor.get_line()+1}:{cursor.get_line_offset()+1}")

    def jump_line(self, line):
        page = self.current()
        if not page:
            return
        self.preview_button.set_active(False)
        result = page.buffer.get_iter_at_line(line)
        iterator = result[-1] if isinstance(result, tuple) else result
        page.buffer.place_cursor(iterator)
        page.editor.scroll_to_iter(iterator, 0.15, True, 0, 0.2)
        page.editor.grab_focus()

    def choose_file(self):
        chooser = Gtk.FileDialog(title="Открыть текст")
        if self.folder:
            chooser.set_initial_folder(Gio.File.new_for_path(str(self.folder)))
        def done(dialog, result):
            try:
                chosen = dialog.open_finish(result)
                if chosen.get_path():
                    self.open_file(Path(chosen.get_path()), True)
            except GLib.Error:
                pass
        chooser.open(self.win, None, done)

    def choose_folder(self):
        chooser = Gtk.FileDialog(title="Открыть папку с текстами")
        if self.folder:
            chooser.set_initial_folder(Gio.File.new_for_path(str(self.folder)))
        def done(dialog, result):
            try:
                chosen = dialog.select_folder_finish(result)
                if chosen.get_path():
                    self.set_folder(Path(chosen.get_path()))
            except GLib.Error:
                pass
        chooser.select_folder(self.win, None, done)

    def save_current(self, save_as=False):
        page = self.current()
        if page:
            self.save_page(page, save_as=save_as)

    def save_page(self, page, callback=None, save_as=False, target=None, overwrite=False):
        page.synchronize()
        doc = page.document
        if target is None and (save_as or doc.path is None):
            dialog = Gtk.FileDialog(title="Сохранить текст", initial_name=doc.title)
            folder = doc.path.parent if doc.path else self.folder or Path.home() / "Documents"
            dialog.set_initial_folder(Gio.File.new_for_path(str(folder)))
            def chosen(chooser, result):
                try:
                    file = chooser.save_finish(result)
                    if not file.get_path():
                        raise ValueError("Выбери локальный файл")
                    path = Path(file.get_path()).resolve()
                    for other in self.pages.values():
                        if other is not page and other.document.path == path:
                            self.error("Этот файл уже открыт", "Выбери другое имя или перейди к открытой вкладке.")
                            if callback:
                                callback(False)
                            return
                    self.save_page(page, callback, target=path)
                except (GLib.Error, ValueError):
                    if callback:
                        callback(False)
            dialog.save(self.win, None, chosen)
            return
        try:
            doc.save(target, overwrite=overwrite)
            page.tab.set_title(doc.title)
            page.tab.set_tooltip(str(doc.path))
            page.update_language()
            self.storage.forget(doc)
            self.persist()
            self.refresh()
            if self.folder:
                self.queue_tree_refresh()
            if callback:
                callback(True)
        except ExternalChangeError as error:
            dialog = Adw.AlertDialog(heading="Проверим перед сохранением", body=str(error) + " Твой текст остаётся в редакторе.")
            dialog.add_response("cancel", "Отмена")
            dialog.add_response("copy", "Сохранить копию…")
            dialog.add_response("overwrite", "Перезаписать")
            dialog.set_response_appearance("overwrite", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("copy")
            dialog.set_close_response("cancel")
            def answer(_, response):
                if response == "copy":
                    self.save_page(page, callback, save_as=True)
                elif response == "overwrite":
                    self.save_page(page, callback, target=target, overwrite=True)
                elif callback:
                    callback(False)
            dialog.connect("response", answer)
            dialog.present(self.win)
        except (OSError, UnicodeError, ValueError) as error:
            self.error("Не удалось сохранить", str(error))
            if callback:
                callback(False)

    def queue_checkpoint(self):
        if self.draft_timer:
            GLib.source_remove(self.draft_timer)
        self.draft_timer = GLib.timeout_add(650, self.persist)

    def persist(self):
        self.draft_timer = 0
        try:
            session = []
            for page in self.pages.values():
                page.synchronize()
                self.storage.checkpoint(page.document)
                if page.document.path:
                    session.append({"path": str(page.document.path), "cursor": page.document.cursor})
            self.storage.save_json("session.json", session)
            self.storage.save_json("settings.json", self.settings)
        except OSError as error:
            self.toast("Не удалось записать черновик: " + str(error))
        return False

    def restore_session(self):
        folder = self.settings.get("folder")
        if folder and Path(folder).is_dir():
            self.set_folder(Path(folder))
        recovered = self.storage.recover()
        recovered_paths = {doc.path for doc in recovered if doc.path}
        for item in self.storage.read_json("session.json", []):
            path = Path(item.get("path", ""))
            if path.is_file() and path not in recovered_paths:
                try:
                    doc = Document.load(path)
                    doc.cursor = item.get("cursor", 0)
                    self.add_document(doc)
                except (OSError, ValueError, UnicodeError):
                    continue
        for doc in recovered:
            self.add_document(doc)
        if recovered:
            self.toast(f"Восстановлены черновики: {len(recovered)}")
        if not self.pages:
            self.new_document()

    def ask_unsaved(self, page, callback):
        page.synchronize()
        if not page.document.dirty:
            callback("clean")
            return
        self.tabs.set_selected_page(page.tab)
        dialog = Adw.AlertDialog(heading="Сохранить изменения?", body=page.document.title)
        dialog.add_response("cancel", "Отмена")
        dialog.add_response("discard", "Не сохранять")
        dialog.add_response("save", "Сохранить")
        dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")
        dialog.set_close_response("cancel")
        def answer(_, response):
            if response == "save":
                self.save_page(page, lambda ok: callback("saved" if ok else "cancel"))
            else:
                callback(response)
        dialog.connect("response", answer)
        dialog.present(self.win)

    def close_page(self, view, tab):
        page = self.pages.get(tab)
        if not page:
            return False
        def answer(response):
            if response == "cancel":
                view.close_page_finish(tab, False)
            else:
                self.storage.forget(page.document)
                view.close_page_finish(tab, True)
        self.ask_unsaved(page, answer)
        return True

    def detached(self, view, tab, position):
        self.pages.pop(tab, None)
        if self.preview_page == tab:
            self.preview_page = None
        self.queue_checkpoint()
        self.refresh()

    def close_window(self, _):
        if self.allow_close:
            return False
        if self.closing_window:
            return True
        self.closing_window = True
        self.persist()
        remaining = list(self.pages.values())
        discarded = []
        def advance():
            if not remaining:
                self.persist()
                for doc in discarded:
                    self.storage.forget(doc)
                self.allow_close = True
                # GTK suppresses recursive close() inside close-request. Let the
                # current emission finish before requesting the approved close.
                GLib.idle_add(self.win.close)
                return
            page = remaining.pop(0)
            def answer(response):
                if response == "cancel":
                    self.closing_window = False
                else:
                    if response == "discard":
                        discarded.append(page.document)
                    advance()
            self.ask_unsaved(page, answer)
        advance()
        return True

    def shutdown_app(self, _):
        self.stopping = True
        for timer in [self.draft_timer, self.spell_timer, self.refresh_timer]:
            if timer:
                GLib.source_remove(timer)
        self.pool.shutdown(wait=False, cancel_futures=True)

    def terminate(self):
        self.persist()
        self.quit()
        return False

    def context_menu(self, page, corrections=None):
        extra = Gio.Menu()
        formatting = Gio.Menu()
        for title, kind in FORMATS:
            formatting.append(title, "win.format-" + kind)
        extra.append_submenu("Форматирование", formatting)
        if corrections:
            start, end, suggestions = corrections
            choices = Gio.Menu()
            for suggestion in suggestions:
                item = Gio.MenuItem.new(suggestion, None)
                item.set_action_and_target_value("win.spell-replace", GLib.Variant("(iis)", (start, end, suggestion)))
                choices.append_item(item)
            if suggestions:
                extra.append_submenu("Исправить слово", choices)
        page.editor.set_extra_menu(extra)

    def context_at(self, page, x, y):
        bx, by = page.editor.window_to_buffer_coords(Gtk.TextWindowType.WIDGET, int(x), int(y))
        result = page.editor.get_iter_at_location(bx, by)
        iterator = result[-1] if isinstance(result, tuple) else result
        offset = iterator.get_offset()
        corrections = None
        for match in spelling.WORD.finditer(page.text()):
            if match.start() <= offset <= match.end() and match[0] in page.spelling:
                corrections = (match.start(), match.end(), page.spelling[match[0]])
                break
        self.context_menu(page, corrections)

    def replace_spelling(self, action, parameter):
        page = self.current()
        if not page:
            return
        start, end, word = parameter.unpack()
        self.replace_range(page, start, end, word)

    def replace_range(self, page, start, end, text):
        buf = page.buffer
        buf.begin_user_action()
        try:
            a, b = buf.get_iter_at_offset(start), buf.get_iter_at_offset(end)
            buf.delete(a, b)
            buf.insert(buf.get_iter_at_offset(start), text)
        finally:
            buf.end_user_action()
        buf.select_range(buf.get_iter_at_offset(start + len(text)), buf.get_iter_at_offset(start))

    def format_selection(self, kind):
        page = self.current()
        if not page:
            return
        selection = page.buffer.get_selection_bounds()
        cursor = page.buffer.get_iter_at_mark(page.buffer.get_insert()).get_offset()
        start, end = (selection[0].get_offset(), selection[1].get_offset()) if selection else (cursor, cursor)
        text = page.text()
        if not page.document.markdown:
            dialog = Adw.AlertDialog(heading="Создать Markdown-копию?", body="Обычный .txt хранит только текст. Оформление сохраним в новой копии .md, исходный файл останется прежним.")
            dialog.add_response("cancel", "Отмена")
            dialog.add_response("copy", "Создать копию")
            dialog.set_response_appearance("copy", Adw.ResponseAppearance.SUGGESTED)
            dialog.set_default_response("copy")
            dialog.set_close_response("cancel")
            def answer(_, response):
                if response == "copy":
                    copy = self.new_document(text=text, title=Path(page.document.title).stem + ".md")
                    self.apply_format(copy, text, start, end, kind)
            dialog.connect("response", answer)
            dialog.present(self.win)
            return
        self.apply_format(page, text, start, end, kind)

    def apply_format(self, page, text, start, end, kind):
        formatted, a, b = format_text(text, start, end, kind)
        # Restrict the edit to the changed region, preserving undo and cursor history.
        prefix = 0
        while prefix < min(len(text), len(formatted)) and text[prefix] == formatted[prefix]:
            prefix += 1
        suffix = 0
        while suffix < min(len(text) - prefix, len(formatted) - prefix) and text[-1 - suffix] == formatted[-1 - suffix]:
            suffix += 1
        self.replace_range(page, prefix, len(text) - suffix, formatted[prefix:len(formatted)-suffix if suffix else None])
        page.buffer.select_range(page.buffer.get_iter_at_offset(b), page.buffer.get_iter_at_offset(a))
        page.editor.grab_focus()

    def queue_spell(self, page):
        page.spell_generation += 1
        if not self.settings.get("spelling", True):
            return
        if self.spell_timer:
            GLib.source_remove(self.spell_timer)
        def run():
            self.spell_timer = 0
            text = page.text()
            generation = page.spell_generation
            future = self.pool.submit(spelling.check, text)
            def completed(job):
                try:
                    result = job.result()
                except Exception:
                    return
                def apply():
                    if self.stopping or page.tab not in self.pages or generation != page.spell_generation:
                        return False
                    page.spelling = result
                    buf = page.buffer
                    buf.remove_tag(page.spell_tag, buf.get_start_iter(), buf.get_end_iter())
                    for match in spelling.WORD.finditer(text[:150000]):
                        if match[0] in result:
                            iterator = buf.get_iter_at_offset(match.start())
                            if not page.buffer.iter_has_context_class(iterator, "no-spell-check"):
                                buf.apply_tag(page.spell_tag, iterator, buf.get_iter_at_offset(match.end()))
                    return False
                GLib.idle_add(apply)
            future.add_done_callback(completed)
            return False
        self.spell_timer = GLib.timeout_add(900, run)

    def show_find(self):
        self.search_reveal.set_reveal_child(True)
        self.find.grab_focus()

    def find_next(self, from_start=False):
        page = self.current()
        query = self.find.get_text()
        if not page or not query:
            return
        self.preview_button.set_active(False)
        buf = page.buffer
        start = buf.get_start_iter() if from_start else buf.get_iter_at_mark(buf.get_insert())
        match = start.forward_search(query, Gtk.TextSearchFlags.CASE_INSENSITIVE, None)
        if not match:
            match = buf.get_start_iter().forward_search(query, Gtk.TextSearchFlags.CASE_INSENSITIVE, None)
        if match:
            a, b = match
            buf.select_range(b, a)
            page.editor.scroll_to_iter(a, 0.15, True, 0, 0.25)

    def replace_text(self, all_matches):
        page = self.current()
        query = self.find.get_text()
        if not page or not query:
            return
        replacement = self.replacement.get_text()
        if all_matches:
            original = page.text()
            text, count = re.subn(re.escape(query), lambda _: replacement, original, flags=re.IGNORECASE)
            if count:
                self.replace_range(page, 0, len(original), text)
            self.toast(f"Заменено: {count}")
        else:
            selection = page.buffer.get_selection_bounds()
            if selection and page.buffer.get_text(*selection, True).casefold() == query.casefold():
                self.replace_range(page, selection[0].get_offset(), selection[1].get_offset(), replacement)
            self.find_next()

    def search_dialog(self, content):
        if not self.folder and content:
            self.toast("Открой папку для поиска по всем текстам.")
            self.choose_folder()
            return
        dialog = Gtk.Window(title="Поиск по папке" if content else "Перейти к файлу", transient_for=self.win, modal=True, default_width=650, default_height=500)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dialog.add_css_class("typer-window")
        header = Gtk.Box(spacing=8)
        header.add_css_class("typer-toolbar")
        header.append(Gtk.Image.new_from_icon_name("preferences-system-search"))
        header.append(label(str(self.folder or "Открытые файлы"), "dim-label"))
        outer.append(header)
        entry = Gtk.SearchEntry(placeholder_text="Фраза в документах…" if content else "Начни вводить имя файла…", margin_start=18, margin_end=18, margin_top=12, margin_bottom=12)
        outer.append(entry)
        results = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        results.add_css_class("boxed-list")
        results.set_margin_start(16)
        results.set_margin_end(16)
        results.set_margin_bottom(16)
        scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
        scroll.set_child(results)
        outer.append(scroll)
        state = {"generation": 0, "timer": 0, "closed": False, "matches": []}
        folder = self.folder
        open_paths = [p.document.path for p in self.pages.values() if p.document.path]
        def collect(query):
            matches = []
            if content and not query:
                return matches
            paths = text_files(folder) if folder else open_paths
            for path in paths:
                try:
                    relative = str(path.relative_to(folder)) if folder else path.name
                    if content:
                        if path.stat().st_size > 2 * 1024 * 1024:
                            continue
                        text = path.read_text(encoding="utf-8-sig")
                        for number, line in enumerate(text.splitlines()):
                            if query in line.casefold():
                                matches.append((path, relative, number, line.strip()[:240]))
                                if len(matches) >= 200:
                                    return matches
                    elif query in relative.casefold():
                        matches.append((path, relative, 0, str(path.parent)))
                        if len(matches) >= 300:
                            return matches
                except (OSError, UnicodeError):
                    continue
            return matches
        def show(matches, generation):
            if state["closed"] or generation != state["generation"] or self.stopping:
                return False
            child = results.get_first_child()
            while child:
                following = child.get_next_sibling()
                results.remove(child)
                child = following
            state["matches"] = matches
            for path, relative, line, snippet in matches:
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, margin_start=12, margin_end=12, margin_top=10, margin_bottom=10)
                box.append(label(relative + (f" · {line+1}" if content else ""), "heading"))
                box.append(label(snippet, "dim-label"))
                row.set_child(box)
                results.append(row)
            if not matches:
                results.append(label("Ничего не найдено" if entry.get_text() else "Введи фразу для поиска" if content else "В папке пока нет текстов", "dim-label"))
            else:
                results.select_row(results.get_row_at_index(0))
            return False
        def update(*_):
            state["generation"] += 1
            generation = state["generation"]
            if state["timer"]:
                GLib.source_remove(state["timer"])
            def submit():
                state["timer"] = 0
                future = self.pool.submit(collect, entry.get_text().casefold())
                def completed(job):
                    try:
                        matches = job.result()
                    except Exception:
                        matches = []
                    GLib.idle_add(show, matches, generation)
                future.add_done_callback(completed)
                return False
            state["timer"] = GLib.timeout_add(180, submit)
        def activate(row):
            if row and row.get_index() < len(state["matches"]):
                path, _, line, _ = state["matches"][row.get_index()]
                self.open_file(path, True)
                if content:
                    self.jump_line(line)
                dialog.close()
        results.connect("row-activated", lambda _, row: activate(row))
        entry.connect("activate", lambda *_: activate(results.get_selected_row()))
        def navigation(_, key, code, modifiers):
            if key == Gdk.KEY_Escape:
                dialog.close()
                return True
            if key in (Gdk.KEY_Down, Gdk.KEY_Up):
                selected = results.get_selected_row()
                index = (selected.get_index() if selected else -1) + (1 if key == Gdk.KEY_Down else -1)
                row = results.get_row_at_index(max(0, index))
                if row:
                    results.select_row(row)
                return True
            return False
        keys = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", navigation)
        dialog.add_controller(keys)
        def closed(*_):
            state["closed"] = True
            if state["timer"]:
                GLib.source_remove(state["timer"])
                state["timer"] = 0
            return False
        dialog.connect("close-request", closed)
        entry.connect("search-changed", update)
        dialog.set_child(outer)
        update()
        dialog.present()
        entry.grab_focus()

    def open_link(self, page, uri):
        parsed = urlparse(uri)
        if parsed.scheme in {"https", "http", "mailto"}:
            Gio.AppInfo.launch_default_for_uri(uri, None)
            return True
        if not parsed.scheme and page.document.path:
            target = page.document.path.parent / unquote(parsed.path)
            if target.is_file():
                self.open_file(target, True)
        return True

    def preferences(self):
        window = Adw.PreferencesWindow(title="Настройки Typer", transient_for=self.win, modal=True, default_width=600, default_height=500)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Текст и управление", description="Цвета, шрифты и оформление следуют текущей теме angelOS.")
        adjustment = Gtk.Adjustment(value=self.settings.get("font_size", 16), lower=10, upper=32, step_increment=1)
        row = Adw.SpinRow(title="Размер текста", adjustment=adjustment)
        row.connect("notify::value", lambda w, _: self.setting("font_size", int(w.get_value())))
        group.add(row)
        spell = Adw.SwitchRow(title="Проверка орфографии", subtitle="Русский и английский. Исправления — в правом меню.", active=self.settings.get("spelling", True))
        spell.connect("notify::active", lambda w, _: self.setting("spelling", w.get_active()))
        group.add(spell)
        swipe = Adw.SwitchRow(title="Переключение вкладок свайпом", subtitle="При передаче жестов тачпада в angelOS.", active=self.settings.get("swipe", True))
        swipe.connect("notify::active", lambda w, _: self.setting("swipe", w.get_active()))
        group.add(swipe)
        if self.folder:
            favorite = Adw.ActionRow(title="Закрепить текущую папку", subtitle=str(self.folder))
            favorite.add_suffix(button("Закрепить", "starred-symbolic", lambda _: self.favorite(True)))
            group.add(favorite)
        page.add(group)
        window.add(page)
        window.present()

    def setting(self, key, value):
        self.settings[key] = value
        if key == "font_size":
            self.apply_font()
        if key == "spelling":
            for page in self.pages.values():
                if value:
                    self.queue_spell(page)
                else:
                    page.spell_generation += 1
                    page.spelling = {}
                    page.buffer.remove_tag(page.spell_tag, page.buffer.get_start_iter(), page.buffer.get_end_iter())
        self.queue_checkpoint()

    def about(self):
        dialog = Adw.AboutDialog(application_name="AngelOS Typer", application_icon=APP_ID, version=__version__, developer_name="AngelOS Typer contributors", comments="Простой редактор текста и Markdown в стиле angelOS.", license_type=Gtk.License.MIT_X11)
        dialog.present(self.win)

    def toggle_sidebar(self):
        self.sidebar.set_visible(not self.sidebar.get_visible())

    def toggle_focus(self):
        self.focus_mode = not self.focus_mode
        self.sidebar.set_visible(not self.focus_mode)
        self.tabbar.set_visible(not self.focus_mode)
        self.outline.set_visible(self.outline_button.get_active() and not self.focus_mode)

    def swipe(self, gesture, vx, vy):
        if self.settings.get("swipe", True) and abs(vx) > 250 and abs(vx) > abs(vy) * 2:
            if vx < 0:
                self.tabs.select_next_page()
            else:
                self.tabs.select_previous_page()

    def scroll_tabs(self, controller, dx, dy):
        if not self.settings.get("swipe", True) or abs(dx) <= abs(dy) * 1.8 or not dx:
            return False
        now = time.monotonic()
        if now - getattr(self, "last_horizontal", 0) > 0.25:
            self.horizontal_amount = 0
        self.last_horizontal = now
        if now < getattr(self, "horizontal_cooldown", 0):
            return True
        self.horizontal_amount = getattr(self, "horizontal_amount", 0) + dx
        unit = controller.get_unit()
        threshold = 60 if unit == Gdk.ScrollUnit.SURFACE else 1.5
        if abs(self.horizontal_amount) >= threshold:
            if self.horizontal_amount > 0:
                self.tabs.select_next_page()
            else:
                self.tabs.select_previous_page()
            self.horizontal_amount = 0
            self.horizontal_cooldown = now + 0.6
        return True

    def toast(self, text):
        self.toasts.add_toast(Adw.Toast.new(text))

    def error(self, title, text=""):
        dialog = Adw.AlertDialog(heading=title, body=text)
        dialog.add_response("close", "Понятно")
        dialog.present(self.win)

    def key(self, controller, keyval, code, modifiers):
        ctrl = bool(modifiers & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(modifiers & Gdk.ModifierType.SHIFT_MASK)
        key = Gdk.keyval_to_lower(keyval)
        if ctrl and code:
            translated = Gdk.Display.get_default().translate_key(code, modifiers, 0)
            if translated[0]:
                key = Gdk.keyval_to_lower(translated[1])
        if key == Gdk.KEY_F11:
            self.toggle_focus()
            return True
        if key == Gdk.KEY_Escape:
            if self.focus_mode:
                self.toggle_focus()
            elif self.search_reveal.get_reveal_child():
                self.search_reveal.set_reveal_child(False)
                if self.current():
                    self.current().editor.grab_focus()
            else:
                return False
            return True
        if not ctrl:
            return False
        if key == Gdk.KEY_p:
            self.search_dialog(False)
        elif key == Gdk.KEY_o:
            self.choose_folder() if shift else self.choose_file()
        elif key == Gdk.KEY_f and shift:
            self.search_dialog(True)
        elif key in (Gdk.KEY_f, Gdk.KEY_h):
            self.show_find()
        elif key == Gdk.KEY_n:
            self.new_document()
        elif key == Gdk.KEY_s:
            self.save_current(shift)
        elif key == Gdk.KEY_w:
            tab = self.tabs.get_selected_page()
            if tab:
                self.tabs.close_page(tab)
        elif key == Gdk.KEY_m and shift:
            self.preview_button.set_active(not self.preview_button.get_active())
        elif key == Gdk.KEY_b:
            self.toggle_sidebar()
        elif key == Gdk.KEY_Tab:
            self.tabs.select_previous_page() if shift else self.tabs.select_next_page()
        else:
            return False
        return True


def main():
    return Typer().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
