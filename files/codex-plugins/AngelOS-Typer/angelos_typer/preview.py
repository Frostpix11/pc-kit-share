"""Local Markdown preview: no browser, scripts or network requests."""
import html
import re
from gi.repository import Gtk, Pango


def inline(text):
    value = html.escape(text)
    # Protect inline code from the other markup substitutions.
    code = []
    def protect(match):
        code.append("<tt>" + match[1] + "</tt>")
        return "\x01" + str(len(code) - 1) + "\x02"
    value = re.sub(r"`([^`]+)`", protect, value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"~~(.+?)~~", r"<s>\1</s>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    value = re.sub(r"(?<!!)\[([^\]]+)\]\(([^\s)]+)\)", r'<a href="\2">\1</a>', value)
    return re.sub(r"\x01(\d+)\x02", lambda m: code[int(m[1])], value)


def render(box, text, link_callback):
    child = box.get_first_child()
    while child:
        following = child.get_next_sibling()
        box.remove(child)
        child = following
    code = None
    for line in text.splitlines():
        if line.startswith("```"):
            if code is None:
                code = []
            else:
                widget = Gtk.Label(label="\n".join(code), xalign=0, selectable=True, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR)
                widget.add_css_class("monospace")
                box.append(widget)
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if not line.strip():
            space = Gtk.Box(height_request=6)
            box.append(space)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        content = heading[2] if heading else line
        content = re.sub(r"^\s*- \[ \] ", "☐  ", content)
        content = re.sub(r"^\s*- \[[xX]\] ", "☑  ", content)
        content = re.sub(r"^\s*[-*+] ", "•  ", content)
        quote = content.startswith("> ")
        if quote:
            content = "│  " + content[2:]
        label = Gtk.Label(xalign=0, selectable=True, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR, hexpand=True)
        label.set_markup(inline(content))
        label.connect("activate-link", lambda _, uri: link_callback(uri))
        if heading:
            label.add_css_class("title-1" if len(heading[1]) == 1 else "title-3")
            label.set_margin_top(8)
        if quote:
            label.add_css_class("dim-label")
        box.append(label)
    if code is not None:
        label = Gtk.Label(label="\n".join(code), xalign=0, selectable=True, wrap=True)
        label.add_css_class("monospace")
        box.append(label)
