"""A banner in the middle of the screen when a rare item drops (owner: B).

"You found: X." in the message corner is easy to miss. A rare, epic or legendary item gets this
instead, with its picture, its name in its rarity colour, a pulsing glow and a fanfare
(the "rare_loot" sound in data/sounds.json). Common and uncommon items only get the message.
"""
import pygame

from core import settings
from core.strings import t
from ui import anim, theme, widgets
from ui.item_info import RARITY_COLORS, item_icon

RARE = ("rare", "epic", "legendary")
SECONDS = 2.4            # how long the banner stays
FADE_SECONDS = 0.35      # it fades in and out this fast
SIZE = (520, 150)
ICON_SCALE = 2           # the item picture is drawn twice as big as in the bag
GLOW = 14                # how far the coloured glow reaches out around the banner, in pixels


def is_rare(item) -> bool:
    return item.get("rarity") in RARE


class LootBanner:
    def __init__(self, item, fonts):
        color = RARITY_COLORS.get(item["rarity"], theme.TEXT)
        self.color = color
        self.rect = pygame.Rect((0, 0), SIZE)
        self.rect.center = (settings.SCREEN_W // 2, settings.SCREEN_H // 3)
        # Everything is drawn once onto one picture; draw() only fades and glows it.
        self.picture = pygame.Surface(SIZE, pygame.SRCALPHA)
        self.picture.fill((20, 18, 22, 235))
        pygame.draw.rect(self.picture, color, self.picture.get_rect(), 3)
        icon = item_icon(item, fonts["small"])
        icon = pygame.transform.scale(icon, (icon.get_width() * ICON_SCALE, icon.get_height() * ICON_SCALE))
        self.picture.blit(icon, icon.get_rect(midleft=(20, SIZE[1] // 2)))
        x = 40 + icon.get_width()
        widgets.text(self.picture, fonts["normal"], t("loot_rare_banner", rarity=t(f"rarity_{item['rarity']}")),
                     theme.TEXT_DIM, (x, 28))
        widgets.text(self.picture, fonts["big"], item["name"], color, (x, 62))
        self.glow = pygame.Surface((SIZE[0] + 2 * GLOW, SIZE[1] + 2 * GLOW), pygame.SRCALPHA)
        for i in range(GLOW, 0, -2):                     # rings that get fainter further out
            alpha = round(90 * (1 - i / GLOW))
            pygame.draw.rect(self.glow, (*color, alpha), self.glow.get_rect().inflate(-2 * (GLOW - i), -2 * (GLOW - i)),
                             2, border_radius=8)
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    def alive(self) -> bool:
        return self.time < SECONDS

    def opacity(self) -> float:
        """0 to 1: fades in at the start and out at the end."""
        return max(0.0, min(1.0, self.time / FADE_SECONDS, (SECONDS - self.time) / FADE_SECONDS))

    def draw(self, surface):
        strength = self.opacity()
        self.glow.set_alpha(round(255 * strength * (0.5 + 0.5 * anim.pulse(1.5))))
        surface.blit(self.glow, self.glow.get_rect(center=self.rect.center))
        self.picture.set_alpha(round(255 * strength))
        surface.blit(self.picture, self.rect)
