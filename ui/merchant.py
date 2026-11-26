"""The shopkeeper, drawn with a small idle animation (used in the shop and on the dungeon map).

There is only one picture of him (assets/sprites/npc_merchant.png), so the animation is made
in code, like the attacks:
  - he breathes: his picture gets a little taller and shorter, slowly
  - he bobs up and down a little with each breath
  - when you buy or sell something he hops with joy (react())
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


class Merchant:
    def __init__(self, scale):
        self.scale = scale
        self.image = assets.load_sprite("npc_merchant", scale)    # None if there is no such art
        self.hopped = -10.0                                       # when he last hopped (long ago)

    def react(self):
        """Hop once, e.g. after a sale."""
        self.hopped = anim.now()

    def frame(self):
        """This moment's picture of him and how far he is lifted up, as (image, lift in screen pixels)."""
        if self.image is None:
            return None, 0
        breath = (math.sin(anim.now() * 2 * math.pi / BREATH_SECONDS) + 1) / 2     # 0 .. 1 .. 0
        width, height = self.image.get_size()
        tall = round(height * (1 + BREATH_STRETCH * breath))
        image = pygame.transform.scale(self.image, (width, tall))
        lift = BOB_PIXELS * self.scale * breath
        hop = (anim.now() - self.hopped) / HOP_SECONDS
        if 0 <= hop < 1:
            lift += HOP_PIXELS * self.scale * math.sin(math.pi * hop)      # up, then down again
        return image, round(lift)

    def draw(self, surface, midbottom):
        """Draw him standing with his feet at `midbottom` (x, y)."""
        image, lift = self.frame()
        if image is not None:
            x, y = midbottom
            surface.blit(image, image.get_rect(midbottom=(x, y - lift)))
