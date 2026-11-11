"""The row of slots at the bottom of the screen (owner: B).

Each entry is a dict: {"icon": Surface, "enabled": bool, "tooltip": [(text, colour), ...]}.
Right now the entries are the player's moves. Phase 4 can add item slots the same way.
"""
import pygame

from core import settings
from ui import slots, theme, tooltip

GAP = 8


class Hotbar:
    def __init__(self, center_x=settings.SCREEN_W // 2, bottom=settings.SCREEN_H - 10):
        self.center_x = center_x
        self.bottom = bottom
        self.entries = []
        self.rects = []

    def set_entries(self, entries):
        """Replace what the hotbar shows and work out where each slot goes."""
        self.entries = entries
        width = len(entries) * slots.SLOT + (len(entries) - 1) * GAP
        left = self.center_x - width // 2
        top = self.bottom - slots.SLOT
        self.rects = [pygame.Rect(left + i * (slots.SLOT + GAP), top, slots.SLOT, slots.SLOT)
                      for i in range(len(entries))]

    def index_at(self, pos):
        """Which slot is under pos (a mouse position)? None if there is none."""
        for i, rect in enumerate(self.rects):
            if rect.collidepoint(pos):
                return i
        return None

    def draw(self, surface, fonts, mouse_pos, selected=None, active=True):
        """active=False greys every slot out (e.g. while a question is on screen)."""
        if not self.rects:
            return
        back = self.rects[0].union(self.rects[-1]).inflate(20, 20)
        pygame.draw.rect(surface, theme.OUTLINE, back)
        pygame.draw.rect(surface, theme.STONE, back.inflate(-4, -4))
        for i, (rect, entry) in enumerate(zip(self.rects, self.entries)):
            slots.draw_slot(surface, rect, entry["icon"], key=str(i + 1), font=fonts["small"],
                            enabled=active and entry["enabled"], highlighted=(i == selected))
        hovered = self.index_at(mouse_pos)
        if hovered is not None:   # drawn last, so the tooltip is on top of the slots
            tooltip.draw_tooltip(surface, fonts["small"], self.entries[hovered]["tooltip"], self.rects[hovered])
