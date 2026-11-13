from pathlib import Path
import os
import re
import shutil
import subprocess

WORD = re.compile(r"[^\W\d_]+(?:[-’'][^\W\d_]+)*", re.UNICODE)


def dictionaries():
    roots = [Path(__file__).resolve().parent.parent / "assets/dictionaries", Path.home() / ".local/share/hunspell", Path("/usr/share/hunspell"), Path("/usr/share/myspell/dicts")]
    result = []
    for names in [("ru_RU",), ("en_US", "en_US-large")]:
        for root in roots:
            found = next((name for name in names if (root / (name + ".dic")).is_file() and (root / (name + ".aff")).is_file()), None)
            if found:
                result.append(str(root / found))
                break
    return result


def check(text):
    paths = dictionaries()
    if not paths or not shutil.which("hunspell"):
        return {}
    # Prefix each line so document contents cannot become Hunspell commands.
    data = "\n".join("^" + line for line in text[:150000].splitlines()) + "\n"
    result = subprocess.run(["hunspell", "-a", "-i", "UTF-8", "-d", ",".join(paths)], input=data, capture_output=True, text=True, timeout=15, env=dict(os.environ, LC_ALL="C.UTF-8"))
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Не удалось проверить орфографию")
    mistakes = {}
    for line in result.stdout.splitlines():
        if line.startswith("& "):
            left, _, right = line.partition(": ")
            parts = left.split()
            if len(parts) >= 2:
                mistakes[parts[1]] = right.split(", ")[:6]
        elif line.startswith("# "):
            parts = line.split()
            if len(parts) >= 2:
                mistakes[parts[1]] = []
    return mistakes
