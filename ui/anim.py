"""Small helpers that make the UI move (owner: B).

They all read the clock themselves (pygame.time.get_ticks), so a screen can use them
inside draw() without keeping any timers of its own.
"""
import math

import pygame

from ui import theme


def now():
    """Seconds since the game started."""
    return pygame.time.get_ticks() / 1000


def pulse(per_second=1.2):
    """A number that swings smoothly between 0 and 1, for things that glow."""
    return (math.sin(now() * per_second * 2 * math.pi) + 1) / 2


def blend(color_a, color_b, amount):
    """A colour between two colours: amount 0 gives color_a, amount 1 gives color_b."""
    return tuple(round(a + (b - a) * amount) for a, b in zip(color_a, color_b))


def glow_gold():
    """The gold of a selected button or slot, gently pulsing brighter and back."""
    return blend(theme.GOLD, theme.GOLD_BRIGHT, pulse())


def ease_out(progress):
    """Turn steady progress (0 to 1) into fast-then-slow progress, for things sliding into place."""
    return 1 - (1 - progress) ** 3


class Trail:
    """A value that follows another value with a delay.

    Used for bars: when HP drops, the bar jumps to the new value at once and a
    lighter "trail" shrinks after it, so the player sees how much was lost.
    """
    SPEED = 3.0   # share of the gap closed per second

    def __init__(self, value):
        self.shown = float(value)
        self.last = now()

    def follow(self, target):
        """Move towards target (by time passed since the last call) and return the trail's value."""
        time = now()
        step = min(1.0, (time - self.last) * self.SPEED)
        self.last = time
        if self.shown > target:
            self.shown += (target - self.shown) * step
            if self.shown - target < 0.5:
                self.shown = float(target)
        else:
            self.shown = float(target)      # going up (healing): no trail
        return self.shown


class FloatingText:
    """A short text that rises and fades, e.g. "-25" over a fighter that was hit."""
    SECONDS = 0.9
    RISE = 46      # pixels it travels upwards

    def __init__(self, font, string, color, center):
        self.image = font.render(string, True, color)     # made once, not every frame
        self.center = center
        self.start = now()

    def alive(self):
        return now() - self.start < self.SECONDS

    def draw(self, surface):
        progress = min(1.0, (now() - self.start) / self.SECONDS)
        self.image.set_alpha(round(255 * (1 - progress ** 2)))   # stays clear, then fades quickly
        x, y = self.center
        surface.blit(self.image, self.image.get_rect(center=(x, y - self.RISE * ease_out(progress))))
