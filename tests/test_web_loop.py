"""The browser loop (pygbag) runs the same frames as the desktop loop and gives control back."""
import asyncio
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from core.game import Game  # noqa: E402


def test_the_web_loop_runs_frames_and_stops():
    game = Game()
    frames = []
    real_frame = game.frame

    def counted():
        real_frame()
        frames.append(1)
        if len(frames) == 5:
            game.quit()
    game.frame = counted
    asyncio.run(game.run_async())
    assert len(frames) == 5


def test_main_does_not_start_the_web_loop_on_the_desktop():
    import main
    assert main.IN_BROWSER is False


def test_main_imports_pygame_itself():
    # pygbag reads main.py's own imports to know it must download pygame for the browser.
    from pathlib import Path
    source = Path(__file__).resolve().parent.parent.joinpath("main.py").read_text(encoding="utf-8")
    assert "\nimport pygame" in source
