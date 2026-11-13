from pathlib import Path
from gi.repository import Gtk, Adw, Gdk, Gio, Pango, GtkSource
from .core import TEXT_SUFFIXES, IGNORED


def label(text, css=None):
    widget = Gtk.Label(label=text, xalign=0, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR, hexpand=True)
    if css:
        widget.add_css_class(css)
    return widget


def icon_image(name):
    image = Gtk.Image.new_from_icon_name(name)
    image.set_pixel_size(16)
    return image


def button(text, icon, callback, tooltip=None):
    widget = Gtk.Button(tooltip_text=tooltip or text)
    content = Gtk.Box(spacing=7)
    if icon:
        content.append(icon_image(icon))
    if text:
        content.append(Gtk.Label(label=text))
    widget.set_child(content)
    widget.connect("clicked", callback)
    return widget


def clear(box):
    child = box.get_first_child()
    while child:
        following = child.get_next_sibling()
        box.remove(child)
        child = following


class DocumentPage:
    def __init__(self, document):
        self.document = document
        self.permanent = True
        self.spelling = {}
        self.spell_generation = 0
        self.stack = Gtk.Stack(hexpand=True, vexpand=True)
        self.buffer = GtkSource.Buffer()
        self.buffer.set_enable_undo(True)
        self.buffer.set_text(document.text)
        self.buffer.set_modified(document.dirty)
        self.editor = GtkSource.View(buffer=self.buffer, wrap_mode=Gtk.WrapMode.WORD_CHAR, left_margin=28, right_margin=28, top_margin=24, bottom_margin=28, pixels_above_lines=2, pixels_below_lines=2, hexpand=True, vexpand=True)
        self.editor.set_auto_indent(True)
        self.editor.set_insert_spaces_instead_of_tabs(True)
        self.editor.set_tab_width(4)
        self.editor.add_css_class("typer-editor")
        language = GtkSource.LanguageManager.get_default().guess_language(str(document.path or document.title), None)
        self.buffer.set_language(language)
        self.editor.set_show_line_numbers(False)
        self.scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
        self.scroll.set_child(self.editor)
        self.stack.add_named(self.scroll, "edit")
        self.preview = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_start=30, margin_end=30, margin_top=22, margin_bottom=30)
        preview_scroll = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
        preview_scroll.set_child(self.preview)
        self.stack.add_named(preview_scroll, "preview")
        self.spell_tag = self.buffer.create_tag("typer-spelling", underline=Pango.Underline.ERROR)
        self.tab = None

    def text(self):
        return self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), True)

    def synchronize(self):
        self.document.text = self.text()
        self.document.cursor = self.buffer.get_iter_at_mark(self.buffer.get_insert()).get_offset()

    def update_language(self):
        self.buffer.set_language(GtkSource.LanguageManager.get_default().guess_language(str(self.document.path or self.document.title), None))


class FolderTree:
    def __init__(self, box, open_file, report_error):
        self.box = box
        self.open_file = open_file
        self.report_error = report_error
        self.monitors = []

    def reset(self):
        for monitor in self.monitors:
            monitor.cancel()
        self.monitors.clear()
        clear(self.box)

    def load(self, folder):
        self.reset()
        self.populate(self.box, Path(folder))

    def populate(self, box, folder):
        try:
            entries = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
        except OSError as error:
            box.append(label(str(error), "dim-label"))
            return
        for path in entries[:500]:
            if path.name.startswith(".") or path.name in IGNORED:
                continue
            if path.is_dir():
                if path.is_symlink():
                    continue
                expander = Gtk.Expander(margin_start=12, margin_end=6, margin_top=5, margin_bottom=5)
                row = Gtk.Box(spacing=8)
                row.append(icon_image("folder"))
                row.append(Gtk.Label(label=path.name, xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE))
                expander.set_label_widget(row)
                expander.set_tooltip_text(str(path))
                child = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=12)
                expander.set_child(child)
                expander.connect("notify::expanded", lambda widget, _, c=child, p=path: self.expand(widget, c, p))
                box.append(expander)
            elif path.suffix.lower() in TEXT_SUFFIXES or not path.suffix:
                box.append(self.file_button(path))
        if len(entries) > 500:
            box.append(label("Больше файлов — через поиск по имени", "dim-label"))

    def expand(self, widget, child, path):
        if widget.get_expanded():
            clear(child)
            self.populate(child, path)

    def file_button(self, path, favorite=False):
        widget = Gtk.Button(tooltip_text=str(path), margin_start=6, margin_end=6)
        widget.add_css_class("flat")
        row = Gtk.Box(spacing=8, margin_top=5, margin_bottom=5)
        row.append(icon_image("folder-favorites" if favorite else "text-markdown" if Path(path).suffix.lower() in {".md", ".markdown"} else "text-x-generic"))
        name = Gtk.Label(label=Path(path).name, xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.MIDDLE)
        row.append(name)
        widget.set_child(row)
        widget.connect("clicked", lambda _: self.open_file(Path(path), False))
        gesture = Gtk.GestureClick()
        gesture.connect("pressed", lambda _, count, x, y: self.open_file(Path(path), True) if count == 2 else None)
        widget.add_controller(gesture)
        return widget
