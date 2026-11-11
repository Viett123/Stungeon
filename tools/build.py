"""Builds Stungeon into a folder that runs without Python installed (for the exhibit laptop).

    pip install -r requirements-build.txt
    python tools/build.py

The result is dist/Stungeon/. Copy that whole folder; start Stungeon.exe inside it.
The game's data files are copied in too, because the exe cannot read them from the repo.
"""
import os
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent

# (file or folder in the repo, folder inside the build). Keep in step with where the code looks.
DATA = [
    ("data", "data"),
    ("questions/data/questions_german_b1.json", "questions/data"),
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

PyInstaller.__main__.run(args)
