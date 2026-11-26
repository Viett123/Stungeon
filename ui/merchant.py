"""The shopkeeper, drawn with an idle animation (used in the shop and on the dungeon map).

He is the dwarf from 0x72's pack: npc_merchant_idle_0.png ... _3.png, played in a loop.
Without those pictures, the one still picture npc_merchant.png is used and the animation is
made in code instead:
  - he breathes: his picture gets a little taller and shorter, slowly
  - he bobs up and down a little with each breath
In both cases he hops with joy when you buy or sell something (react()).
"""
import math

import pygame

from core import assets
from ui import anim

BREATH_SECONDS = 2.4      # one breath in and out
BREATH_STRETCH = 0.04     # how much taller he gets at the top of a breath (4 %)
BOB_PIXELS = 2            # how far he bobs up with each breath, in art pixels
HOP_SECONDS = 0.35        # how long the happy hop lasts
HOP_PIXELS = 6            # how high he hops, in art pixels
IDLE_FPS = 6              # pictures per second of the idle animation


class Merchant:
    def __init__(self, scale, facing_left=False):
        """facing_left: mirror him (the art looks right), e.g. to face the shop's item list."""
        self.scale = scale
        self.frames = assets.load_frames("npc_merchant_idle", scale)  # the animation (empty without art)
        if facing_left:
            self.frames = [pygame.transform.flip(frame, True, False) for frame in self.frames]
        self.image = assets.load_sprite("npc_merchant", scale)    # the still picture, None if there is none
        self.hopped = -10.0                                       # when he last hopped (long ago)

    def react(self):
        """Hop once, e.g. after a sale."""
        self.hopped = anim.now()

    def frame(self):
        """This moment's picture of him and how far he is lifted up, as (image, lift in screen pixels)."""
        hop = (anim.now() - self.hopped) / HOP_SECONDS
        hop_lift = HOP_PIXELS * self.scale * math.sin(math.pi * hop) if 0 <= hop < 1 else 0   # up, then down again
        if self.frames:
            image = self.frames[int(anim.now() * IDLE_FPS) % len(self.frames)]
            return image, round(hop_lift)
        if self.image is None:
            return None, 0
        breath = (math.sin(anim.now() * 2 * math.pi / BREATH_SECONDS) + 1) / 2     # 0 .. 1 .. 0
        width, height = self.image.get_size()
        tall = round(height * (1 + BREATH_STRETCH * breath))
        image = pygame.transform.scale(self.image, (width, tall))
        lift = BOB_PIXELS * self.scale * breath + hop_lift
        return image, round(lift)

    def draw(self, surface, midbottom):
        """Draw him standing with his feet at `midbottom` (x, y)."""
        image, lift = self.frame()
        if image is not None:
            x, y = midbottom
            surface.blit(image, image.get_rect(midbottom=(x, y - lift)))
