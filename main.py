"""Starts Stungeon.

    python main.py                 normal window
    python main.py --fullscreen    for the exhibit laptop
    python main.py --demo          skip the title menu and start the exhibit demo at once
    python main.py --frames 120    run 120 frames, then quit (used by the smoke test)

In a web browser (built with pygbag, see docs/WEB.md) there are no options, and the game runs
with run_async() so the page does not freeze.
"""
import argparse
import asyncio
import sys

import pygame  # noqa: F401  pygbag only downloads the packages main.py itself imports

from core import flow
from core.game import Game

IN_BROWSER = sys.platform == "emscripten"   # pygbag runs Python as WebAssembly ("emscripten")


def main():
    parser = argparse.ArgumentParser(description="Stungeon")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--demo", action="store_true", help="start the demo run immediately")
    parser.add_argument("--frames", type=int, default=0, help="quit after this many frames (0 = never)")
    args = parser.parse_args()
    game = Game(fullscreen=args.fullscreen)
    if args.demo:
        flow.start_demo(game)
    game.run(max_frames=args.frames)


async def main_web():
    await Game().run_async()


if IN_BROWSER:
    asyncio.run(main_web())
elif __name__ == "__main__":
    main()
