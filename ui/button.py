"""A clickable rectangle with a label (owner: B)."""
import pygame

from ui import anim, theme, widgets


class Button:
    def __init__(self, rect, label, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.enabled = enabled

    def hit(self, pos):
        """True if pos (a mouse position) is on this button and it can be used."""
        return self.enabled and self.rect.collidepoint(pos)

    def draw(self, surface, font, mouse_pos, selected=False):
        hover = self.hit(mouse_pos)
        pygame.draw.rect(surface, theme.OUTLINE, self.rect)
        fill = theme.STONE if (hover or selected) else theme.SLOT_FILL
        pygame.draw.rect(surface, fill, self.rect.inflate(-4, -4))
        if selected:
            pygame.draw.rect(surface, anim.glow_gold(), self.rect.inflate(-4, -4), width=2)   # gently pulsing
        if not self.enabled:
            color = theme.DISABLED
        else:
            color = theme.GOLD if selected else theme.TEXT
        # The label of the button under the mouse, or of the selected one, sits a little to the right.
        nudge = 6 if (hover or selected) else 0
        widgets.text(surface, font, self.label, color, (self.rect.x + 14 + nudge, self.rect.centery), "midleft")
