#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATCH_DIR = ROOT / "tools" / "defs_patch" / "ethereum" / "chains"
DEST_DIR = ROOT / "common" / "defs" / "ethereum" / "chains" / "_data" / "chains"


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for patch_file in sorted(PATCH_DIR.glob("eip155-*.json")):
        # Validate the patch file before copying it into defs.
        json.loads(patch_file.read_text())
        shutil.copy2(patch_file, DEST_DIR / patch_file.name)


if __name__ == "__main__":
    main()
