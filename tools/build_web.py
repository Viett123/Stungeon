"""Builds the web version of Stungeon with pygbag (see docs/WEB.md).

    python tools/build_web.py            -> build/web_dist/stungeon/build/web/ and build/stungeon_web.zip
    python tools/build_web.py --serve    -> the same, then play it at http://localhost:8000

What it does, step by step:
  1. Copies only what the game needs into a clean folder: no tests, tools, docs, logs or saves.
  2. Turns every sound into OGG with ffmpeg (browsers can't play every WAV; core/sound.py
     takes the .ogg when it is there).
  3. Runs pygbag on the copy. Its output (index.html, stungeon.apk, favicon.png) is zipped,
     ready to upload to itch.io.
Needs: pip install pygbag, and ffmpeg on the PATH.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import version  # noqa: E402

OUT = ROOT / "build" / "web_dist"
APP = OUT / "stungeon"
FOLDERS = ["ai", "combat", "core", "data", "dungeon", "systems", "ui", "assets"]
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc")


def copy_game():
    if OUT.exists():
        shutil.rmtree(OUT)
    APP.mkdir(parents=True)
    shutil.copy2(ROOT / "main.py", APP / "main.py")
    for folder in FOLDERS:
        shutil.copytree(ROOT / folder, APP / folder, ignore=SKIP)
    # The question engine and its banks, but not the build scripts or the review CSVs.
    (APP / "questions" / "data").mkdir(parents=True)
    for file in (ROOT / "questions").glob("*.py"):
        shutil.copy2(file, APP / "questions" / file.name)
    for file in (ROOT / "questions" / "data").glob("*.json"):
        shutil.copy2(file, APP / "questions" / "data" / file.name)
    # The browser has no git, so the version's patch number is counted now (core/version.py).
    version.write_stamp(APP / "core" / "build_stamp.json")


def sounds_to_ogg():
    for wav in sorted((APP / "assets" / "sounds").glob("*.wav")):
        ogg = wav.with_suffix(".ogg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis",
                        "-q:a", "5", str(ogg)], check=True)
        wav.unlink()


def build(serve):
    command = [sys.executable, "-m", "pygbag", "--title", "Stungeon"]
    if not serve:
        command.append("--build")
    subprocess.run(command + [str(APP)], check=True, cwd=OUT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="after building, serve it at localhost:8000")
    args = parser.parse_args()
    copy_game()
    sounds_to_ogg()
    if args.serve:
        build(serve=True)          # pygbag builds, then keeps serving until you press Ctrl+C
        return
    build(serve=False)
    web = APP / "build" / "web"
    zip_file = shutil.make_archive(str(ROOT / "build" / "stungeon_web"), "zip", web)
    print("Built version", version.number(version.read_stamp(APP / "core" / "build_stamp.json")),
          ":", web, "and", zip_file)


if __name__ == "__main__":
    main()
