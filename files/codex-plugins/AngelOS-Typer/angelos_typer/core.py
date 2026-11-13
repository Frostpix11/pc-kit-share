"""File handling and recovery, independent of the graphical interface."""
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import os
import re
import tempfile
import uuid

MAX_FILE_SIZE = 20 * 1024 * 1024
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".log", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".py", ".sh", ".css", ".html", ".js", ".qml", ".kdl", ".patch", ".csv", ".xml"}
IGNORED = {".git", ".venv", "node_modules", "__pycache__", ".cache"}


class ExternalChangeError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data, mode=0o600):
    """Replace a complete file; leave the previous file intact on failure."""
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@dataclass
class Document:
    text: str = ""
    path: Path | None = None
    title: str = "Новый текст.md"
    identifier: str = field(default_factory=lambda: uuid.uuid4().hex)
    encoding: str = "utf-8"
    newline: str = "\n"
    original_digest: str | None = None
    saved_text: str = ""
    cursor: int = 0

    @property
    def dirty(self):
        return self.text != self.saved_text

    @property
    def markdown(self):
        return (self.path.suffix if self.path else Path(self.title).suffix).lower() in {".md", ".markdown"}

    @classmethod
    def load(cls, path):
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise OSError("Файл не найден: " + str(path))
        if path.stat().st_size > MAX_FILE_SIZE:
            raise ValueError("Файл больше 20 МБ. Эта версия рассчитана на обычные текстовые документы.")
        data = path.read_bytes()
        encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig" if data.startswith(b"\xef\xbb\xbf") else "utf-8"
        decoded = data.decode(encoding)
        if "\x00" in decoded:
            raise ValueError("Это не обычный текстовый файл.")
        newline = "\r\n" if "\r\n" in decoded else "\r" if "\r" in decoded else "\n"
        # Mixed line endings are retained until explicitly edited by the user.
        text = decoded.replace("\r\n", "\n").replace("\r", "\n")
        doc = cls(text=text, saved_text=text, path=path, title=path.name, encoding=encoding, newline=newline, original_digest=digest(data))
        doc._original_bytes = data
        return doc

    def save(self, target=None, overwrite=False):
        target = Path(target or self.path).expanduser().resolve()
        same = self.path is not None and target == self.path
        exists = target.exists()
        if same and not overwrite:
            current = digest(target.read_bytes()) if exists else None
            if current != self.original_digest:
                raise ExternalChangeError("Файл изменён другой программой или удалён.")
        elif exists and not overwrite:
            raise ExternalChangeError("Файл с таким именем уже существует.")
        if exists and not os.access(target, os.W_OK):
            raise PermissionError("Нет прав на запись в этот файл.")
        mode = target.stat().st_mode & 0o777 if exists else 0o600
        if same and not self.dirty and hasattr(self, "_original_bytes"):
            data = self._original_bytes
        else:
            data = self.text.replace("\n", self.newline).encode(self.encoding)
        atomic_write(target, data, mode)
        self.path = target
        self.title = target.name
        self.saved_text = self.text
        self.original_digest = digest(data)
        self._original_bytes = data


class Storage:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.drafts = self.directory / "drafts"
        self.drafts.mkdir(exist_ok=True, mode=0o700)

    def save_json(self, name, value):
        atomic_write(self.directory / name, json.dumps(value, ensure_ascii=False, indent=2).encode())

    def read_json(self, name, fallback):
        try:
            return json.loads((self.directory / name).read_text())
        except (OSError, ValueError):
            return fallback

    def checkpoint(self, doc):
        path = self.drafts / (doc.identifier + ".json")
        if not doc.dirty:
            path.unlink(missing_ok=True)
            return
        payload = {key: getattr(doc, key) for key in ["text", "title", "identifier", "encoding", "newline", "original_digest", "saved_text", "cursor"]}
        payload["path"] = str(doc.path) if doc.path else None
        atomic_write(path, json.dumps(payload, ensure_ascii=False).encode())

    def forget(self, doc):
        (self.drafts / (doc.identifier + ".json")).unlink(missing_ok=True)

    def recover(self):
        result = []
        fields = set(Document.__dataclass_fields__)
        for path in sorted(self.drafts.glob("*.json")):
            try:
                data = json.loads(path.read_text())
                data = {key: value for key, value in data.items() if key in fields}
                if not isinstance(data.get("text"), str):
                    continue
                if data.get("path"):
                    data["path"] = Path(data["path"])
                doc = Document(**data)
                if doc.dirty:
                    result.append(doc)
            except (OSError, ValueError, TypeError):
                continue
        return result


def format_text(text, start, end, kind):
    """Return a formatted document and selection in Unicode character offsets."""
    start, end = sorted((start, end))
    if kind in {"bold", "italic", "strike", "code", "link"}:
        selected = text[start:end] or "текст"
        if kind == "link":
            replacement = "[" + selected + "](https://)"
        else:
            mark = {"bold": "**", "italic": "*", "strike": "~~", "code": "`"}[kind]
            replacement = mark + selected + mark
        return text[:start] + replacement + text[end:], start, start + len(replacement)
    a = text.rfind("\n", 0, start) + 1
    last = end - 1 if end > start and text[end - 1:end] == "\n" else end
    b = text.find("\n", last)
    if b < 0:
        b = len(text)
    prefix = {"h1": "# ", "h2": "## ", "h3": "### ", "bullet": "- ", "task": "- [ ] ", "quote": "> "}[kind]
    lines = text[a:b].split("\n")
    if kind.startswith("h"):
        lines = [re.sub(r"^#{1,6}\s+", "", line) for line in lines]
    replacement = "\n".join(prefix + line for line in lines)
    return text[:a] + replacement + text[b:], a, a + len(replacement)


def text_files(folder, limit=10000):
    count = 0
    for base, dirs, names in os.walk(folder, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED and not d.startswith("."))
        for name in sorted(names):
            path = Path(base) / name
            if not name.startswith(".") and (path.suffix.lower() in TEXT_SUFFIXES or not path.suffix):
                yield path
                count += 1
                if count >= limit:
                    return
