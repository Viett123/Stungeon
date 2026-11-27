"""Builds Stungeon into a folder that runs without Python installed (for the exhibit laptop).

    pip install -r requirements-build.txt
    python tools/build.py

The result is dist/Stungeon/. Copy that whole folder; start Stungeon.exe inside it.
The game's data files are copied in too, because the exe cannot read them from the repo.
"""
import os
import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import version  # noqa: E402

# The exe has no git inside, so the version's patch number is counted now (core/version.py)
# and packed into the exe as core/build_stamp.json.
STAMP = ROOT / "build_tmp" / "build_stamp.json"
STAMP.parent.mkdir(exist_ok=True)
version.write_stamp(STAMP)

# (file or folder in the repo, folder inside the build). Keep in step with where the code looks.
DATA = [
    ("data", "data"),
    ("questions/data", "questions/data"),       # every level's question bank (A1, A2, B1, ...)
    ("core/strings_en.json", "core"),
    ("assets", "assets"),
]

args = [
    str(ROOT / "main.py"),
    "--name", "Stungeon",
    "--noconfirm",
    "--windowed",                              # no black console window behind the game
    "--distpath", str(ROOT / "dist"),
    "--workpath", str(ROOT / "build_tmp"),     # not "build": questions/build/ is something else
    "--specpath", str(ROOT / "build_tmp"),
]
for source, target in DATA:
    args += ["--add-data", f"{ROOT / source}{os.pathsep}{target}"]
args += ["--add-data", f"{STAMP}{os.pathsep}core"]

PyInstaller.__main__.run(args)
print("Built version", version.number(version.read_stamp(STAMP)), "in", ROOT / "dist" / "Stungeon")
