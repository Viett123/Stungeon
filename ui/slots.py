"""Square slots (for moves now, items later) and their icons (owner: B)."""
import pygame

from core import assets
from ui import theme, widgets

SLOT = 64          # size of a slot on screen
ICON = 48          # size of the icon inside it (16 px art drawn 3 times bigger)

_icon_cache = {}   # icons are made once, not every frame


def _placeholder_icon(color, letters, font):
    """A coloured square with one or two letters, used until there is icon art."""
    small = pygame.Surface((16, 16))
    small.fill(color)
    pygame.draw.rect(small, theme.OUTLINE, small.get_rect(), width=1)
    darker = tuple(max(0, c - 30) for c in color)
    pygame.draw.line(small, darker, (1, 14), (14, 14))
    icon = assets.scale_up(small)
    mark = font.render(letters, True, theme.TEXT)
    icon.blit(mark, mark.get_rect(center=icon.get_rect().center))
    return icon


def icon_for(name, color, letters, font):
    """The icon assets/sprites/<name>.png, or a placeholder if that file does not exist."""
    if name not in _icon_cache:
        _icon_cache[name] = _load_icon(name) or _placeholder_icon(color, letters, font)
    return _icon_cache[name]


def _load_icon(name):
    """Load the icon as big as possible while it still fits in a slot.

    Most art is 16x16 and fits at 3 times its size. Tall art (a sword is 10x21) does
    not, so it is tried at 2 times and then at its real size.
    """
    for factor in (3, 2, 1):
        image = assets.load_sprite(name, factor)
        if image is None:
            return None
        if image.get_width() <= ICON and image.get_height() <= ICON:
            return image
    return image


def draw_slot(surface, rect, icon=None, key="", font=None, enabled=True, highlighted=False):
    """Draw one slot. key is the small label in the corner (the number key that uses it)."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, theme.OUTLINE, rect)
    pygame.draw.rect(surface, theme.GOLD if highlighted else theme.METAL_DARK, rect.inflate(-4, -4))
    pygame.draw.rect(surface, theme.SLOT_FILL, rect.inflate(-8, -8))
    if icon is not None:
        surface.blit(icon, icon.get_rect(center=rect.center))
        if not enabled:
            # A dark see-through cover shows the slot can't be used right now.
            cover = pygame.Surface(icon.get_size(), pygame.SRCALPHA)
            cover.fill((0, 0, 0, 150))
            surface.blit(cover, cover.get_rect(center=rect.center))
    if key and font:
        widgets.text(surface, font, key, theme.GOLD if enabled else theme.DISABLED, (rect.x + 7, rect.y + 5))
