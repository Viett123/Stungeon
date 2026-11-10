"""Starts Stungeon.

    python main.py                 normal window
    python main.py --fullscreen    for the exhibit laptop
    python main.py --frames 120    run 120 frames, then quit (used by the smoke test)
"""
import argparse

from core.game import Game


def main():
    parser = argparse.ArgumentParser(description="Stungeon")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--frames", type=int, default=0, help="quit after this many frames (0 = never)")
    args = parser.parse_args()
    Game(fullscreen=args.fullscreen).run(max_frames=args.frames)


if __name__ == "__main__":
    main()
