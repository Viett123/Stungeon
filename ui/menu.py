"""A list of choices in a frame, used by the title menu and the pause menu (owner: B).

Each option is (label, action, enabled). action is a function called when the option
is chosen. Up/Down (or W/S) move, Enter chooses, the mouse works too.
"""
import pygame

from core import settings
from core.scene import Scene
from ui import theme, widgets
from ui.button import Button

BUTTON_W, BUTTON_H, GAP = 380, 48, 10
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


class MenuScene(Scene):
    def __init__(self, game, title, options, under=None, top=250):
        super().__init__(game)
        self.title = title
        self.under = under          # the scene to show (darkened) behind the menu, or None
        self.actions = [action for _, action, _ in options]
        left = (settings.SCREEN_W - BUTTON_W) // 2
        self.buttons = [Button((left, top + i * (BUTTON_H + GAP), BUTTON_W, BUTTON_H), label, enabled)
                        for i, (label, _, enabled) in enumerate(options)]
        self.frame = pygame.Rect(left - 50, top - 110, BUTTON_W + 100,
                                 len(options) * (BUTTON_H + GAP) + 150)
        self.selected = next(i for i, b in enumerate(self.buttons) if b.enabled)

    def move(self, step):
        """Go to the next option that can be used, skipping greyed-out ones."""
        for _ in self.buttons:
            self.selected = (self.selected + step) % len(self.buttons)
            if self.buttons[self.selected].enabled:
                return

    def on_escape(self):
        """What Esc does. Menus that can be closed replace this."""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.move(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.move(1)
            elif event.key in ENTER_KEYS:
                self.actions[self.selected]()
            elif event.key == pygame.K_ESCAPE:
                self.on_escape()
        elif event.type == pygame.MOUSEMOTION:
            self.select_at(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.select_at(event.pos):
            self.actions[self.selected]()

    def select_at(self, pos):
        """Select the button under the mouse. Returns True if there is one."""
        for i, button in enumerate(self.buttons):
            if button.hit(pos):
                self.selected = i
                return True
        return False

    def draw(self, surface):
        if self.under:
            self.under.draw(surface)
            widgets.dim(surface)
        fonts = self.game.fonts
        theme.draw_frame(surface, self.frame)
        widgets.text(surface, fonts["big"], self.title, theme.GOLD,
                     (self.frame.centerx, self.frame.y + 56), "center")
        mouse = pygame.mouse.get_pos()
        for i, button in enumerate(self.buttons):
            button.draw(surface, fonts["normal"], mouse, selected=(i == self.selected))
