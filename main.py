"""Starts Stungeon.

    python main.py                 normal window
    python main.py --fullscreen    for the exhibit laptop
    python main.py --demo          skip the title menu and start the exhibit demo at once
    python main.py --frames 120    run 120 frames, then quit (used by the smoke test)
"""
import argparse

from core import flow
from core.game import Game


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


if __name__ == "__main__":
    main()
