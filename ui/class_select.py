"""Choose Warrior, Mage or Archer, then start a new run (owner: B)."""
import pygame

from core import settings
from core.run import new_run
from core.scene import Scene
from core.strings import t
from systems.player import Player, load_data
from ui import widgets

CLASS_IDS = ["warrior", "mage", "archer"]
NUMBER_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3]


class ClassSelectScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.selected = 0
        # Show every move of each class (as if at max level), so the player knows what is coming.
        max_level = load_data("progression.json")["max_level"]
        self.previews = {cid: Player(cid, level=max_level) for cid in CLASS_IDS}
        self.preview_moves = {cid: p.unlocked_moves() for cid, p in self.previews.items()}
        self.starts = {cid: Player(cid) for cid in CLASS_IDS}   # level-1 stats
        self.cards = []   # rects, filled in by draw(), used for mouse clicks

    def start(self):
        from dungeon.dungeon_scene import DungeonScene
        self.game.run_state = new_run(CLASS_IDS[self.selected])
        self.game.scenes.replace(DungeonScene(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(CLASS_IDS)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(CLASS_IDS)
            elif event.key in NUMBER_KEYS:
                self.selected = NUMBER_KEYS.index(event.key)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.start()
            elif event.key == pygame.K_ESCAPE:
                self.game.go_to_title()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.cards):
                if rect.collidepoint(event.pos):
                    if i == self.selected:
                        self.start()
                    self.selected = i

    def draw(self, surface):
        f = self.game.fonts
        cx = settings.SCREEN_W // 2
        widgets.text(surface, f["big"], t("choose_class"), settings.COLOR_TEXT, (cx, 70), "center")
        widgets.text(surface, f["small"], t("class_hint"), settings.COLOR_DIM, (cx, 680), "center")

        self.cards = []
        width, gap = 360, 40
        left = cx - (3 * width + 2 * gap) // 2
        for i, cid in enumerate(CLASS_IDS):
            p = self.previews[cid]
            border = settings.COLOR_HIGHLIGHT if i == self.selected else (80, 70, 100)
            rect = widgets.panel(surface, (left + i * (width + gap), 130, width, 500), border=border)
            self.cards.append(rect)
            pygame.draw.rect(surface, p.color, (rect.centerx - 40, rect.y + 30, 80, 80), border_radius=10)
            widgets.text(surface, f["big"], f"{i + 1}. {p.class_name}", settings.COLOR_TEXT,
                         (rect.centerx, rect.y + 150), "center")
            start = self.starts[cid]
            widgets.text(surface, f["small"], t("class_hp", hp=start.max_hp), settings.COLOR_DIM,
                         (rect.centerx, rect.y + 195), "center")
            widgets.text(surface, f["small"], t("class_resource", resource=p.resource_name, amount=start.max_resource),
                         settings.COLOR_DIM, (rect.centerx, rect.y + 222), "center")
            y = rect.y + 270
            for move in self.preview_moves[cid]:
                widgets.text(surface, f["normal"], move["name"], settings.COLOR_TEXT, (rect.x + 30, y))
                widgets.text(surface, f["small"], t(f"tier_{move['tier']}"), settings.COLOR_DIM, (rect.x + 30, y + 26))
                y += 44
