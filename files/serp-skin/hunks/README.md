# serp-skin hunk sets

One file per area: `hunks/<area>.py` with `HUNKS = {"rel/path/in/shell.qml": [(OLD, NEW), ...]}`.
apply.py merges them. Rules (break them and kit's watcher doubles other patches → shell crash):
- OLD must occur exactly once in the live file; NEW must contain OLD's meaning plus `// serp-skin`.
- Never anchor inside text another pc-kit patch owns: grep ~/pc-kit/files/patches/*/{*.py,*.sh,*.patch}
  for your OLD lines (orig/ backups don't count) — and lines carrying `// vm-patch` / `celestia` marks.
- Gate every change on `Serp.on` (the skin) so Classic and Golden Gate stay exactly as they are.
- Paths starting with "~/" are outside the shell (installed plugins).
