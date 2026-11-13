#!/usr/bin/env python3
"""Expose the plugin's scene to angelOS' Pictures scanner as a symlink; never touch other folders.
   ensure-scene.py PLUGIN_DIR DESIRED_LINK [--remove]"""
import json, sys
from pathlib import Path
plugin = Path(sys.argv[1]).resolve()
desired = Path(sys.argv[2])
target = plugin / "scene"
if "--remove" in sys.argv:
    if desired.is_symlink() and desired.resolve() == target:
        desired.unlink()
    print(json.dumps({"removed": str(desired)}))
    sys.exit()
desired.parent.mkdir(parents=True, exist_ok=True)
candidate, index = desired, 2
while candidate.exists() or candidate.is_symlink():
    if candidate.is_symlink() and candidate.resolve() == target:
        break
    candidate = desired.with_name(desired.name + "-" + str(index)); index += 1
else:
    candidate.symlink_to(target, target_is_directory=True)
print(json.dumps({"dir": str(candidate)}))
