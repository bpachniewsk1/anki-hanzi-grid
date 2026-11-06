# Hanzi Grid, an Anki add-on.
# Copyright (C) 2026 bpachniewsk1
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Build the .ankiaddon package that you upload to AnkiWeb.

    python3 build_ankiaddon.py

An .ankiaddon file is just a zip of the add-on's *contents* (no folder
around them). This script packs only the files the add-on needs, listed
below, so development files (this script, screenshots, __pycache__, your
own meta.json settings …) never end up in the package.

Output: build/hanzi_grid-<version>.ankiaddon, version from manifest.json.
"""

import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Everything that goes into the package. Folders are added recursively.
INCLUDE = [
    "__init__.py",
    "grid_data.py",
    "previewer.py",
    "settings.py",
    "config.json",
    "config.md",
    "manifest.json",
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
    "data",
]

# Never packed, even inside an included folder.
SKIP_NAMES = {"__pycache__", "meta.json", ".DS_Store"}


def files_to_pack():
    for name in INCLUDE:
        path = HERE / name
        if not path.exists():
            raise SystemExit(f"Missing file: {name}")
        paths = [path] if path.is_file() else sorted(path.rglob("*"))
        for file in paths:
            if file.is_file() and not SKIP_NAMES & set(file.relative_to(HERE).parts):
                yield file


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    json.loads((HERE / "config.json").read_text(encoding="utf-8"))  # must be valid JSON
    out = HERE / "build" / f"{manifest['package']}-{manifest['human_version']}.ankiaddon"
    out.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files_to_pack():
            zf.write(file, file.relative_to(HERE).as_posix())

    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    print(f"Built {out.relative_to(HERE)} ({out.stat().st_size // 1024} KB, {len(names)} files):")
    for name in names:
        print("  " + name)


if __name__ == "__main__":
    main()
