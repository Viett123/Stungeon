"""Start the real game without a window for a few frames and check it quits cleanly."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("pygame")
ROOT = Path(__file__).resolve().parent.parent


def test_game_runs_and_quits():
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    result = subprocess.run([sys.executable, "main.py", "--frames", "30"],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
