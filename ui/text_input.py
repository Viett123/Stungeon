"""A one-line box the player types into (owner: B)."""
import pygame

from ui import theme, widgets

MAX_LENGTH = 60


class TextInput:
    def __init__(self, rect=(0, 0, 100, 52)):
        self.rect = pygame.Rect(rect)
        self.text = ""
        self.blink = 0.0   # seconds, used to make the cursor blink

    def clear(self):
        self.text = ""

    def handle_event(self, event):
        """Add typed characters and handle Backspace. Enter is handled by the screen."""
        if event.type == pygame.TEXTINPUT:
            self.text = (self.text + event.text)[:MAX_LENGTH]
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]

    def update(self, dt):
        self.blink += dt

    def draw(self, surface, font):
        pygame.draw.rect(surface, theme.OUTLINE, self.rect)
        pygame.draw.rect(surface, theme.GOLD, self.rect.inflate(-4, -4))
        pygame.draw.rect(surface, theme.SLOT_FILL, self.rect.inflate(-8, -8))
        cursor = "|" if int(self.blink * 2) % 2 == 0 else ""
        widgets.text(surface, font, self.text + cursor, theme.TEXT, (self.rect.x + 16, self.rect.centery), "midleft")
