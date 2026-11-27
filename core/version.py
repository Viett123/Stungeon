"""The game's version, shown small in the bottom-right corner, e.g. "v1.0.84 web".

    1.0   MAJOR_MINOR, changed by hand for a big step (1.1, 2.0, ...)
    84    the patch number: how many commits the code has. It goes up by itself with every
          commit, so nobody has to remember to change it.
    *     after the number: the build had changes that were not committed yet
    web   which kind of build: dev (run from the code with python main.py), exe (tools/build.py)
          or web (tools/build_web.py)

The exe and the web version have no git inside them, so the build scripts count the commits
while building and write the result into core/build_stamp.json (write_stamp below). When the
game runs from the code, it asks git itself. If git is not there, the label is just "v1.0 dev".

No pygame here, so the build scripts can use this file too.
"""
import functools
import json
import subprocess
import sys
from pathlib import Path

MAJOR_MINOR = "1.0"
ROOT = Path(__file__).resolve().parent.parent
STAMP_FILE = Path(__file__).resolve().parent / "build_stamp.json"   # made by the build scripts, not in git


def kind():
    """"web", "exe" or "dev": which kind of build is running."""
    if sys.platform == "emscripten":
        return "web"
    if getattr(sys, "frozen", False):
        return "exe"
    return "dev"


def _git(*args):
    """Run a git command in the project folder. Returns its output, or None if it fails."""
    try:
        done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def from_git():
    """{"patch": number of commits, "changed": True if there are uncommitted changes}, or {}."""
    count = _git("rev-list", "--count", "HEAD")
    if not count or not count.isdigit():
        return {}
    return {"patch": int(count), "changed": bool(_git("status", "--porcelain", "--untracked-files=no"))}


@functools.cache
def _git_once():
    """from_git(), but asked only once: asking git takes a moment, and the answer can't change
    while the game runs."""
    return from_git()


def read_stamp(path=None):
    """The saved build stamp (STAMP_FILE unless another path is given), or {} if there is none."""
    try:
        return json.loads(Path(path or STAMP_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_stamp(path):
    """Used by tools/build.py and tools/build_web.py: save this moment's patch number into a build."""
    Path(path).write_text(json.dumps(from_git()), encoding="utf-8")


def number(stamp=None):
    """ "1.0.84", "1.0.84*" with uncommitted changes, or "1.0" if the patch is unknown."""
    if stamp is None:
        stamp = read_stamp() or (_git_once() if kind() == "dev" else {})
    if "patch" not in stamp:
        return MAJOR_MINOR
    return f"{MAJOR_MINOR}.{stamp['patch']}" + ("*" if stamp.get("changed") else "")
