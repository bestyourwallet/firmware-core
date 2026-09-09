#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def load_entries(path: Path) -> list[dict]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} does not contain a JSON array")
    return data


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage: merge_compile_commands.py OUTPUT INPUT [INPUT ...]",
            file=sys.stderr,
        )
        return 2

    output = Path(sys.argv[1]).resolve()
    inputs = [Path(arg).resolve() for arg in sys.argv[2:]]

    merged: dict[tuple[str, str], dict] = {}
    for path in inputs:
        for entry in load_entries(path):
            key = (entry.get("file", ""), entry.get("output", ""))
            merged[key] = entry

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w") as f:
        json.dump(list(merged.values()), f, indent=4)
        f.write("\n")

    print(f"merged {len(inputs)} databases into {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
