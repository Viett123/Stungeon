"""A character on the map that is drawn with animation (owner: A).

The game rules only know which TILE a character is on. An Actor is the picture of
that character: it glides to the new tile instead of jumping, plays the run frames
while it moves and the idle frames while it stands, and faces the way it walks.
"""
import pygame

from core import settings
from dungeon import sprites

TILE = settings.TILE
SECONDS_PER_FRAME = 0.12      # how long each animation frame is shown
ACTIONS = ("idle", "run", "hit", "attack", "die", "use")   # a character without one of these uses idle
PLAYER_SPEED = 480            # pixels per second the player's picture glides (10 tiles a second)


class Animation:
    """A list of pictures shown one after another, over and over."""

    def __init__(self, frames, seconds_per_frame=SECONDS_PER_FRAME):
        self.frames = frames
        self.seconds_per_frame = seconds_per_frame
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    def index(self):
        return int(self.time / self.seconds_per_frame) % len(self.frames)

    def image(self):
        return self.frames[self.index()]


def _flipped(frames):
    """The same pictures mirrored, for a character that faces left."""
    return [pygame.transform.flip(frame, True, False) for frame in frames]


class Actor:
    def __init__(self, tile, frames_by_action, speed=PLAYER_SPEED):
        """frames_by_action: {"idle": [...], "run": [...]} and optionally the other ACTIONS."""
        self.x, self.y = tile[0] * TILE, tile[1] * TILE      # where the picture is now, in world pixels
        self.target = (self.x, self.y)                       # where it is gliding to
        self.speed = speed
        self.facing_left = False
        self.moving = False
        # Mirror every frame once here, so nothing has to be flipped while the game runs.
        self.animations = {action: (Animation(frames), Animation(_flipped(frames)))
                           for action, frames in frames_by_action.items()}

    def move_to(self, tile):
        """Start gliding to a tile and turn to face it."""
        new_x = tile[0] * TILE
        if new_x != self.target[0]:
            self.facing_left = new_x < self.target[0]
        self.target = (new_x, tile[1] * TILE)

    def face(self, tile):
        """Turn towards a tile without moving (e.g. towards an enemy that blocks the way)."""
        if tile[0] * TILE != self.target[0]:
            self.facing_left = tile[0] * TILE < self.target[0]

    def update(self, dt):
        step = self.speed * dt
        self.x = _approach(self.x, self.target[0], step)
        self.y = _approach(self.y, self.target[1], step)
        self.moving = (self.x, self.y) != self.target
        for right, left in self.animations.values():
            right.update(dt)
            left.update(dt)

    def image(self, action=None):
        """The picture to draw now. Without an action: run while moving, otherwise idle."""
        action = action or ("run" if self.moving else "idle")
        right, left = self.animations.get(action) or self.animations["idle"]
        return (left if self.facing_left else right).image()

    def image_at(self, action, progress):
        """A picture of an animation that plays ONCE (attack, die, use an item).

        progress goes from 0.0 (the first picture) to 1.0 (the last picture, which then stays).
        """
        right, left = self.animations.get(action) or self.animations["idle"]
        frames = (left if self.facing_left else right).frames
        return frames[min(int(progress * len(frames)), len(frames) - 1)]

    def feet(self):
        """The point on the floor the character stands on: bottom middle of its tile, in world pixels."""
        return self.x + TILE // 2, self.y + TILE

    def center(self):
        return self.x + TILE // 2, self.y + TILE // 2


def _approach(value, target, step):
    """Move value towards target by at most step, without going past it."""
    if value < target:
        return min(value + step, target)
    return max(value - step, target)


def make_actor(name, tile, color, letter="", font=None, big=False, speed=PLAYER_SPEED):
    """Build an Actor from the art files of a character (see assets/README.md for the names)."""
    frames = {action: sprites.character_frames(name, action, color, letter, font, big)
              for action in ACTIONS}
    return Actor(tile, frames, speed)
