"""Between two floors: pick one of a few risk-and-reward choices (owner: B).

The choices and what they do are in data/choices.json and systems/choices.py.
This file only shows them as cards and reads input.
"""
import pygame

from core import flow, settings
from core.scene import Scene
from core.strings import t
from systems import choices
from ui import theme, widgets

CARD_W, CARD_H, GAP = 340, 300, 30
NUMBER_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


class ChoiceScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.run = game.run_state
        self.options = choices.offer(self.run.rng)
        self.selected = 0
        total = len(self.options) * CARD_W + (len(self.options) - 1) * GAP
        left = (settings.SCREEN_W - total) // 2
        self.cards = [pygame.Rect(left + i * (CARD_W + GAP), 210, CARD_W, CARD_H) for i in range(len(self.options))]

    def take(self, index):
        choices.apply(self.options[index], self.run)
        flow.go_to_next_floor(self.game)

    def handle_event(self, event):
        count = len(self.options)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % count
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % count
            elif event.key in NUMBER_KEYS[:count]:
                self.selected = NUMBER_KEYS.index(event.key)
            elif event.key in ENTER_KEYS:
                self.take(self.selected)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, card in enumerate(self.cards):
                if card.collidepoint(event.pos):
                    if i == self.selected:
                        self.take(i)         # clicking the selected card again takes it
                        return
                    self.selected = i

    def draw(self, surface):
        fonts = self.game.fonts
        cx = settings.SCREEN_W // 2
        player = self.run.player
        widgets.text(surface, fonts["big"], t("choice_title"), theme.GOLD, (cx, 90), "center")
        status = t("hp_label", hp=player.hp, max_hp=player.max_hp) + "     " + t("shop_gold", gold=player.gold)
        widgets.text(surface, fonts["normal"], status, theme.TEXT, (cx, 140), "center")
        for i, (card, option) in enumerate(zip(self.cards, self.options)):
            inside = theme.draw_frame(surface, card, highlight=(i == self.selected))
            widgets.text(surface, fonts["normal"], f"{i + 1}. {option['name']}", theme.GOLD, (inside.centerx, inside.y + 8), "midtop")
            widgets.wrapped(surface, fonts["small"], option["text"], theme.TEXT, (inside.x + 6, inside.y + 70), inside.width - 12)
        widgets.text(surface, fonts["small"], t("choice_hint"), theme.TEXT_DIM, (cx, 580), "center")
