"""Fixed technical settings. Balancing numbers do NOT go here: they go in data/*.json."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"

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
