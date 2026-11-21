"""How each move looks in a fight: arcs, flying orbs, falling meteors, rings (owner: B).

This is ONLY a picture. It never changes damage or effects; those rules are in
combat/damage.py and combat/effects.py. Which look a move has (kind, colour, size, ...)
is written in data/skill_looks.json, so it can be changed without touching code.

Four kinds of look, all drawn in code with simple shapes:
  slash       arcs cut across the enemy when the hit lands (more arcs for stronger moves)
  projectile  an orb or a streak flies from the hand to the enemy, leaving sparks behind
  rain        several orbs or streaks fall onto the enemy from above
  aura        a ring grows around the player (utility moves, which do not attack)
Every look ends with a burst of sparks in its colour where it lands.

A look runs on its own clock, from 0.0 (start) to 1.0 (end). For attacks it uses the
same timing as the weapon swing (dungeon/weapon.py), so the hit lands at IMPACT.

To add a new kind: write a _draw_<kind> method and use the kind's name in the JSON.
"""
import math
import random

import pygame

from dungeon.weapon import IMPACT, STRIKE_START
from systems.player import load_data

AURA_SECONDS = 0.8          # how long the ring of a utility move lasts
SPARK_SECONDS = 0.5         # how long one spark of a burst lives
SPARKS_PER_BURST = 14       # sparks in a burst at size 1.0
RAIN_HEIGHT = 260           # how far above the enemy rain starts, in pixels
SLASH_START = IMPACT - 0.1  # the first arc appears just before the hit lands
KINDS = ("slash", "projectile", "rain", "aura")

_looks = None               # data/skill_looks.json, read the first time it is needed


def look_for(move_id):
    """The look of a move, from data/skill_looks.json (the "default" look if it has none)."""
    global _looks
    if _looks is None:
        _looks = load_data("skill_looks.json")
    look = dict(_looks["default"])
    look.update(_looks["looks"].get(move_id, {}))
    return look


def _lighter(color, amount=90):
    return tuple(min(255, c + amount) for c in color)


class SkillLook:
    def __init__(self, move_id, start, target, seconds, rng=None):
        """start: where it comes from (the player's hand, or the player for an aura).
        target: where it lands (the enemy's middle). seconds: how long it plays."""
        self.move_id = move_id
        self.look = look_for(move_id)
        self.kind = self.look["kind"] if self.look["kind"] in KINDS else "slash"
        self.color = tuple(self.look["color"])
        self.size = self.look.get("size", 1.0)
        self.count = max(1, self.look.get("count", 1))
        self.start = start
        self.target = target
        self.seconds = seconds
        self.time = 0.0
        self.rng = rng or random.Random()
        self.sparks = []        # [x, y, speed x, speed y, seconds left]
        self.trail = []         # sparks left behind by a flying projectile, same shape
        self.landed = 0         # how many of the falling things have landed (rain), or 1 when hit
        # Rain: each falling thing gets its own spot over the enemy and its own moment to land.
        self.drops = [(self.rng.uniform(-60, 60), STRIKE_START + (IMPACT - STRIKE_START) * (i + 1) / self.count)
                      for i in range(self.count)]

    # --- the clock ---------------------------------------------------------
    @property
    def progress(self):
        return min(1.0, self.time / self.seconds)

    def alive(self):
        return self.progress < 1.0 or bool(self.sparks)

    def update(self, dt):
        before = self.progress
        self.time += dt
        now = self.progress
        if self.kind == "rain":
            for offset, lands in self.drops[self.landed:]:
                if now >= lands:                           # this one just reached the enemy
                    self.burst((self.target[0] + offset, self.target[1]), 0.6)
                    self.landed += 1
        elif self.kind != "aura" and before < IMPACT <= now:
            self.burst(self.target, 1.0)
        if self.kind == "projectile" and STRIKE_START <= now < IMPACT and self.rng.random() < 0.7:
            x, y = self.projectile_spot()
            self.trail.append([x, y, self.rng.uniform(-30, 30), self.rng.uniform(-30, 30), SPARK_SECONDS * 0.6])
        for spark in self.sparks + self.trail:
            spark[0] += spark[2] * dt
            spark[1] += spark[3] * dt
            spark[3] += 120 * dt                           # sparks fall a little, like real ones
            spark[4] -= dt
        self.sparks = [s for s in self.sparks if s[4] > 0]
        self.trail = [s for s in self.trail if s[4] > 0]

    def burst(self, center, strength):
        """Sparks flying out in every direction from where the hit landed."""
        for _ in range(round(SPARKS_PER_BURST * self.size * strength)):
            angle = self.rng.uniform(0, 2 * math.pi)
            speed = self.rng.uniform(80, 220) * self.size
            self.sparks.append([center[0], center[1], math.cos(angle) * speed, math.sin(angle) * speed,
                                SPARK_SECONDS * self.rng.uniform(0.5, 1.0)])

    def finish(self):
        """The player skipped ahead (pressed Enter): stop at once."""
        self.time = self.seconds
        self.sparks, self.trail = [], []

    # --- drawing -----------------------------------------------------------
    def draw(self, surface):
        getattr(self, f"_draw_{self.kind}")(surface)
        for x, y, _, _, left in self.sparks + self.trail:
            size = 4 if left > SPARK_SECONDS * 0.5 else 2  # sparks shrink as they burn out
            pygame.draw.rect(surface, _lighter(self.color, 60), (round(x), round(y), size, size))

    def projectile_spot(self):
        """Where the projectile is now, on the straight line from the hand to the enemy."""
        travelled = (self.progress - STRIKE_START) / (IMPACT - STRIKE_START)
        travelled = max(0.0, min(1.0, travelled))
        return (self.start[0] + (self.target[0] - self.start[0]) * travelled,
                self.start[1] + (self.target[1] - self.start[1]) * travelled)

    def _draw_thing(self, surface, center, direction):
        """One orb or one streak at `center`, moving in `direction` (a pair, about length 1)."""
        x, y = center
        if self.look.get("shape") == "streak":
            length = 34 * self.size
            tail = (x - direction[0] * length, y - direction[1] * length)
            pygame.draw.line(surface, self.color, tail, center, max(2, round(4 * self.size)))
            pygame.draw.circle(surface, _lighter(self.color), (round(x), round(y)), max(2, round(3 * self.size)))
        else:
            radius = 9 * self.size
            pygame.draw.circle(surface, self.color, (round(x), round(y)), round(radius))
            pygame.draw.circle(surface, _lighter(self.color), (round(x), round(y)), round(radius * 0.6))
            pygame.draw.circle(surface, (255, 255, 255), (round(x), round(y)), max(1, round(radius * 0.25)))

    def _draw_projectile(self, surface):
        if not STRIKE_START <= self.progress < IMPACT:
            return
        dx, dy = self.target[0] - self.start[0], self.target[1] - self.start[1]
        length = math.hypot(dx, dy) or 1
        self._draw_thing(surface, self.projectile_spot(), (dx / length, dy / length))

    def _draw_rain(self, surface):
        for i, (offset, lands) in enumerate(self.drops):
            leaves = lands - (IMPACT - STRIKE_START) * 0.6       # each one falls for a short while
            if not leaves <= self.progress < lands:
                continue
            fallen = (self.progress - leaves) / (lands - leaves)
            x = self.target[0] + offset - 40 * (1 - fallen)       # falls slightly slanted
            y = self.target[1] - RAIN_HEIGHT * (1 - fallen)
            self._draw_thing(surface, (x, y), (0.15, 0.99))

    def _draw_slash(self, surface):
        """Arcs across the enemy, one after another. The first one is there when the hit lands."""
        for i in range(self.count):
            begins = SLASH_START + i * 0.12
            shown = (self.progress - begins) / 0.25               # each arc lives for a quarter of the attack
            if not 0.0 <= shown < 1.0:
                continue
            radius = 60 * self.size
            rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            rect.center = self.target
            tilt = i * 1.1                                        # each arc is cut at a different angle
            sweep = 2.4 * min(1.0, shown * 2)                     # the arc grows, then fades
            width = max(2, round(8 * self.size * (1 - shown)))
            pygame.draw.arc(surface, self.color, rect, tilt, tilt + sweep, width)
            pygame.draw.arc(surface, _lighter(self.color), rect.inflate(-6, -6), tilt, tilt + sweep, max(1, width // 2))

    def _draw_aura(self, surface):
        """Two rings growing out from the player and fading."""
        for delay in (0.0, 0.25):
            grown = (self.progress - delay) / 0.75
            if not 0.0 <= grown < 1.0:
                continue
            radius = round(20 + 90 * self.size * grown)
            width = max(1, round(6 * (1 - grown)))
            pygame.draw.circle(surface, self.color, (round(self.start[0]), round(self.start[1])), radius, width)
