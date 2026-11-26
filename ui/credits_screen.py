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
COLUMN_GAP = 40           # space between the two columns
ENTRY_GAP = 10            # space between two entries
LINE_GAP = 2              # space between the lines of one entry
LIST_TOP = 58             # where the list starts, under the title
HINT_SPACE = 34           # room kept free at the bottom for the hint
CLOSE_KEYS = (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class CreditsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.entries = load_data("credits.json")["credits"]     # read once, not in draw()
        self.layout = self.make_layout()

    def make_layout(self):
        """Where every line goes: [(font name, text, colour, (x, y))], worked out once.

        The entries fill the left column from top to bottom, then the right column, so the
        list always fits on the screen, even when more people are added to credits.json.
        Long lines are wrapped to the width of a column.
        """
        fonts = self.game.fonts
        inside = theme.inner(PANEL)
        width = (inside.width - COLUMN_GAP) // 2
        top, bottom = inside.y + LIST_TOP, inside.bottom - HINT_SPACE
        layout, column, y = [], 0, top
        for entry in self.entries:
            parts = [entry["pack"], t("credits_by", author=entry["author"])]
            if entry["license"]:
                parts.append(entry["license"])
            lines = [("normal", line, theme.TEXT, 0) for line in widgets.wrap(fonts["normal"], entry["what"], width)]
            lines += [("small", line, theme.TEXT_DIM, 12) for line in widgets.wrap(fonts["small"], " - ".join(parts), width - 12)]
            height = sum(fonts[font].get_height() + LINE_GAP for font, _, _, _ in lines)
            if y + height > bottom and y > top and column == 0:
                column, y = 1, top                           # this column is full: go on in the next one
            x = inside.x + column * (width + COLUMN_GAP)
            for font, line, color, indent in lines:
                layout.append((font, line, color, (x + indent, y)))
                y += fonts[font].get_height() + LINE_GAP
            y += ENTRY_GAP
        return layout

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CLOSE_KEYS:
            self.game.go_to_title()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.game.go_to_title()

    def draw(self, surface):
        fonts = self.game.fonts
        inside = theme.draw_frame(surface, PANEL)
        widgets.text(surface, fonts["big"], t("credits_title"), theme.GOLD, inside.topleft)
        for font, line, color, pos in self.layout:
            widgets.text(surface, fonts[font], line, color, pos)
        widgets.text(surface, fonts["small"], t("credits_hint"), theme.TEXT_DIM, inside.bottomleft, "bottomleft")
