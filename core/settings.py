"""Fixed technical settings. Balancing numbers do NOT go here: they go in data/*.json."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FONT_DIR = ROOT / "assets" / "fonts"

# The pixel font VT323 (free, SIL Open Font License, see assets/CREDITS.md). It can draw English,
# German (ä ö ü ß) and Vietnamese. Every text uses it (26 Nov 2026: the chunky Tiny5 title font
# was dropped, VT323 looks best and is easier to read). Only the size changes.
FONTS = {
    "title": ("VT323-Regular.ttf", 80),
    "big": ("VT323-Regular.ttf", 40),
    "normal": ("VT323-Regular.ttf", 28),
    "small": ("VT323-Regular.ttf", 22),
    # Questions and answers: big, because this is the text players must read fast.
    # A question that needs more than 2 lines at "question" size uses "question_small"
    # (combat/combat_scene.py).
    "question": ("VT323-Regular.ttf", 44),
    "question_small": ("VT323-Regular.ttf", 34),
    "answer": ("VT323-Regular.ttf", 34),
}
OLD_FONT_SIZES = {"title": 96, "big": 48, "normal": 32, "small": 26,
                  "question": 48, "question_small": 38, "answer": 36}   # pygame's built-in font, if a file is missing

# Where the game may write files (logs). In a built exe (tools/build.py) the code lives in a
# hidden folder, so we write next to Stungeon.exe instead, where people can find the log.
FROZEN = getattr(sys, "frozen", False)
WRITE_DIR = Path(sys.executable).parent if FROZEN else ROOT
LOG_DIR = WRITE_DIR / "logs"

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

TILE_SRC = 16                 # size of a tile in the art files
TILE_SCALE = 3
TILE = TILE_SRC * TILE_SCALE  # 48 px on screen

# Placeholder colours until real art exists (R, G, B)
COLOR_BG = (16, 14, 14)   # same as ui/theme.py BACKGROUND
COLOR_TEXT = (235, 230, 220)
COLOR_DIM = (140, 130, 150)
COLOR_WALL = (60, 52, 72)
COLOR_FLOOR = (34, 28, 42)
COLOR_STAIRS = (200, 170, 60)
COLOR_PLAYER = (90, 180, 230)
COLOR_GOOD = (110, 210, 120)
COLOR_BAD = (230, 90, 90)
COLOR_HP = (200, 70, 70)
COLOR_RESOURCE = (220, 180, 60)
COLOR_HIGHLIGHT = (255, 220, 120)
COLOR_DISABLED = (90, 84, 100)

MESSAGE_SECONDS = 3.0   # how long a message stays on the dungeon screen
