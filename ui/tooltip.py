"""A small box of text that appears next to the thing the mouse is over (owner: B)."""
import pygame

from ui import theme, widgets

PAD = 10
LINE_GAP = 4


def tooltip_rect(size, anchor, screen):
    """Where a tooltip of `size` goes: above `anchor`, centred, and never off the screen."""
    rect = pygame.Rect((0, 0), size)
    rect.midbottom = (anchor.centerx, anchor.top - 6)
    if rect.top < screen.top:           # no room above: put it below instead
        rect.top = anchor.bottom + 6
    return rect.clamp(screen)


def draw_tooltip(surface, font, lines, anchor):
    """lines is a list of (text, colour). anchor is the rect of the thing being explained."""
    if not lines:
        return
    images = [font.render(widgets.drawable(string), True, color) for string, color in lines]
    width = max(image.get_width() for image in images) + 2 * PAD
    height = sum(image.get_height() + LINE_GAP for image in images) - LINE_GAP + 2 * PAD
    rect = tooltip_rect((width, height), pygame.Rect(anchor), surface.get_rect())
    pygame.draw.rect(surface, theme.OUTLINE, rect)
    pygame.draw.rect(surface, theme.METAL_DARK, rect.inflate(-4, -4))
    pygame.draw.rect(surface, theme.PANEL_FILL, rect.inflate(-8, -8))
    y = rect.y + PAD
    for image in images:
        surface.blit(image, (rect.x + PAD, y))
        y += image.get_height() + LINE_GAP
