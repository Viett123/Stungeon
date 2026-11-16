"""Choose Warrior, Mage or Archer; next comes the dungeon screen (owner: B)."""
import pygame

from core import flow, settings
from core.scene import Scene
from core.strings import t
from systems.player import Player, load_data
from dungeon.actor import make_actor
from dungeon.weapon import HeldWeapon
from ui import move_info, slots, theme, widgets
from ui.backdrop import Backdrop

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
        self.backdrop = Backdrop()
        self.selected = CLASS_IDS.index(game.new_game["class_id"]) if game.new_game.get("class_id") in CLASS_IDS else 0
        # Pictures are made once here, never inside draw().
        font = game.fonts["small"]
        self.actors = {cid: make_actor(f"player_{cid}", (0, 0), p.color, big=True)
                       for cid, p in self.previews.items()}
        classes = load_data("classes.json")["classes"]
        self.weapons = {cid: HeldWeapon(classes[cid]["start_weapon"], settings.TILE_SCALE + 1)
                        for cid in CLASS_IDS if classes[cid].get("start_weapon")}
        self.icons = {cid: [self.small_icon(move, font) for move in moves]
                      for cid, moves in self.preview_moves.items()}

    def small_icon(self, move, font):
        """A move's icon, shrunk to fit the small slots in the move list."""
        icon = slots.icon_for(f"icon_{move['id']}", theme.TIER_COLORS[move["tier"]],
                              move_info.initials(move["name"]), font)
        return pygame.transform.scale(icon, (32, 32))

    def start(self):
        flow.class_chosen(self.game, CLASS_IDS[self.selected])

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
                flow.show_name_screen(self.game)     # back one screen, keeping the name
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.cards):
                if rect.collidepoint(event.pos):
                    if i == self.selected:
                        self.start()
                    self.selected = i

    def update(self, dt):
        self.backdrop.update(dt)
        for actor in self.actors.values():
            actor.update(dt)     # keeps the idle animation playing

    def draw(self, surface):
        f = self.game.fonts
        cx = settings.SCREEN_W // 2
        self.backdrop.draw(surface)
        widgets.text(surface, f["big"], t("choose_class"), theme.OUTLINE, (cx + 3, 73), "center")
        widgets.text(surface, f["big"], t("choose_class"), theme.GOLD, (cx, 70), "center")
        widgets.text(surface, f["small"], t("class_hint"), theme.TEXT_DIM, (cx, 680), "center")

        self.cards = []
        width, gap = 360, 40
        left = cx - (3 * width + 2 * gap) // 2
        for i, cid in enumerate(CLASS_IDS):
            p = self.previews[cid]
            rect = pygame.Rect(left + i * (width + gap), 130, width, 510)
            theme.draw_frame(surface, rect, highlight=(i == self.selected))
            self.cards.append(rect)
            image = self.actors[cid].image()
            feet = (rect.centerx, rect.y + 120)
            surface.blit(image, image.get_rect(midbottom=feet))
            weapon = self.weapons.get(cid)
            if weapon and weapon.has_art:
                weapon.draw(surface, feet, facing_left=False)     # the weapon this class starts with
            widgets.text(surface, f["big"], f"{i + 1}. {p.class_name}", theme.TEXT,
                         (rect.centerx, rect.y + 150), "center")
            start = self.starts[cid]
            widgets.text(surface, f["small"], t("class_hp", hp=start.max_hp), theme.TEXT_DIM,
                         (rect.centerx, rect.y + 195), "center")
            widgets.text(surface, f["small"], t("class_resource", resource=p.resource_name, amount=start.max_resource),
                         theme.TEXT_DIM, (rect.centerx, rect.y + 222), "center")
            y = rect.y + 262
            for move, icon in zip(self.preview_moves[cid], self.icons[cid]):
                slots.draw_slot(surface, (rect.x + 28, y, 44, 44))
                surface.blit(icon, icon.get_rect(center=(rect.x + 50, y + 22)))
                widgets.text(surface, f["normal"], move["name"], theme.TEXT, (rect.x + 86, y))
                widgets.text(surface, f["small"], t(f"tier_{move['tier']}"), theme.TEXT_DIM, (rect.x + 86, y + 24))
                y += 46
