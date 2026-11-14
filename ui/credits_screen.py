"""The Credits screen: who made the art and other parts this game uses (owner: B).

The list is in data/credits.json. Some of the art must be credited (CC BY), so this
screen is part of the game, not just a file in the repo.
"""
import pygame

from core.scene import Scene
from core.strings import t
from systems.player import load_data
from ui import theme, widgets

PANEL = pygame.Rect(120, 30, 1040, 660)
ROW_HEIGHT = 68
CLOSE_KEYS = (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class CreditsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.entries = load_data("credits.json")["credits"]     # read once, not in draw()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CLOSE_KEYS:
            self.game.go_to_title()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.game.go_to_title()

    def draw(self, surface):
        fonts = self.game.fonts
        inside = theme.draw_frame(surface, PANEL)
        widgets.text(surface, fonts["big"], t("credits_title"), theme.GOLD, inside.topleft)
        y = inside.y + 58
        for entry in self.entries:
            widgets.text(surface, fonts["normal"], entry["what"], theme.TEXT, (inside.x, y))
            parts = [entry["pack"], t("credits_by", author=entry["author"])]
            if entry["license"]:
                parts.append(entry["license"])
            widgets.text(surface, fonts["small"], "   -   ".join(parts), theme.TEXT_DIM, (inside.x + 16, y + 30))
            y += ROW_HEIGHT
        widgets.text(surface, fonts["small"], t("credits_hint"), theme.TEXT_DIM, inside.bottomleft, "bottomleft")
