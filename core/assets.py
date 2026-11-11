"""Loads sprite images from assets/sprites/ once and keeps them in memory.

If a file is missing or broken, load_sprite() returns None and the caller draws a
placeholder in code instead. So missing art can never crash the game.

Sprite files are small pixel art (tiles are 16x16) and are drawn 3 times bigger.
See assets/README.md for the file names the game looks for.
"""
import logging

import pygame

from core import settings

SPRITE_DIR = settings.ROOT / "assets" / "sprites"

_cache = {}   # name -> Surface or None, so each file is read from disk only once


def scale_up(image, factor=settings.TILE_SCALE):
    """Make pixel art bigger without blurring it."""
    width, height = image.get_size()
    return pygame.transform.scale(image, (width * factor, height * factor))


def load_sprite(name, factor=settings.TILE_SCALE):
    """Return assets/sprites/<name>.png scaled up, or None if there is no such file."""
    key = (name, factor)
    if key not in _cache:
        _cache[key] = _read(SPRITE_DIR / f"{name}.png", factor)
    return _cache[key]


def load_frames(name, factor=settings.TILE_SCALE):
    """Return the animation frames <name>_0.png, <name>_1.png, ... as a list (empty if there are none)."""
    frames = []
    while True:
        image = load_sprite(f"{name}_{len(frames)}", factor)
        if image is None:
            return frames
        frames.append(image)


def _read(path, factor):
    if not path.exists():
        return None
    try:
        return scale_up(pygame.image.load(str(path)).convert_alpha(), factor)
    except pygame.error:
        # A broken image file: write it to the log and fall back to the placeholder.
        logging.exception("Could not load sprite %s", path)
        return None


def clear_cache():
    """Forget loaded sprites (used by tests)."""
    _cache.clear()
