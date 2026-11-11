"""The dungeon you walk through (owner: A).

Walk into an enemy to fight it. The boss stands on the stairs: beat it, step on the
stairs, and you go down to the next floor. Enemies don't move yet (TODO(C): A* chasing).
"""
import pygame

from core import settings
from core.scene import Scene
from core.strings import t
from dungeon import sprites
from dungeon.camera import Camera
from dungeon.floor import STAIRS, generate_floor
from dungeon.renderer import DungeonRenderer
from systems.enemies import make_enemy
from systems.player import load_data
from ui import hud, move_info, theme
from ui.hotbar import Hotbar

MOVE_KEYS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
# The dungeon fills the whole window. The status panel and hotbar are drawn on top of it.
VIEW = pygame.Rect(0, 0, settings.SCREEN_W, settings.SCREEN_H)


class DungeonScene(Scene):
    def __init__(self, game, messages=None):
        super().__init__(game)
        self.run = game.run_state
        self.floor = generate_floor(self.run.floor_number, seed=self.run.seed)
        self.player_pos = self.floor.start
        # Enemy data (names, colours) loaded once here, not in draw().
        self.enemy_info = {e["id"]: make_enemy(e["id"]) for e in self.floor.enemies}
        # Map letter: first letter of the name, skipping "The" (so bosses aren't all "T").
        self.letter = {eid: next(w for w in info.name.split() if w != "The")[0]
                       for eid, info in self.enemy_info.items()}
        self.messages = []          # [(text, seconds left)]
        for m in messages or []:
            self.say(m)
        if self.run.floor_number == 1:
            self.say(t("dungeon_hint"))   # explain the controls once, at the start of a run

        # Drawing: build everything once here, never inside draw().
        self.renderer = DungeonRenderer(self.floor)
        self.camera = Camera(VIEW.width, VIEW.height, self.renderer.world_w, self.renderer.world_h)
        self.camera.snap_to(*self.player_center())
        font = game.fonts["small"]
        player = self.run.player
        self.player_image = sprites.character_sprite(f"player_{player.class_id}", player.color)
        self.enemy_images = {
            eid: sprites.character_sprite(f"enemy_{eid}", info.color, self.letter[eid], font, big=info.boss)
            for eid, info in self.enemy_info.items()}
        self.hotbar = Hotbar()
        self.refresh_hotbar()

    def refresh_hotbar(self):
        """Show the player's moves in the hotbar. Called at the start and after a level up."""
        player = self.run.player
        entries = move_info.hotbar_entries(player.unlocked_moves(), player.resource_name, self.game.fonts["small"])
        self.hotbar.set_entries(entries)

    def player_center(self):
        """The middle of the player's tile, in world pixels (what the camera follows)."""
        x, y = self.player_pos
        return x * settings.TILE + settings.TILE // 2, y * settings.TILE + settings.TILE // 2

    def say(self, message):
        self.messages.append([message, settings.MESSAGE_SECONDS])
        self.messages = self.messages[-3:]

    # --- input -------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.go_to_title()
        elif event.key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[event.key]
            self.try_move(self.player_pos[0] + dx, self.player_pos[1] + dy)

    def enemy_at(self, pos):
        return next((e for e in self.floor.enemies if e["pos"] == pos), None)

    def try_move(self, x, y):
        if not self.floor.is_walkable(x, y):
            return
        enemy = self.enemy_at((x, y))
        if enemy:
            self.start_fight(enemy)
            return
        self.player_pos = (x, y)
        if self.floor.grid[y][x] == STAIRS:
            self.next_floor()

    # --- fights ------------------------------------------------------------
    def start_fight(self, map_enemy):
        from combat.combat_scene import CombatScene

        def on_end(result):
            self.after_fight(map_enemy, result)

        self.game.scenes.push(CombatScene(self.game, self.run.player, make_enemy(map_enemy["id"]), on_end))

    def after_fight(self, map_enemy, result):
        if result["fled"]:
            self.say(t("fled"))
            return
        if not result["won"]:
            from ui.screens import EndScene
            self.game.scenes.replace(EndScene(self.game, won=False))
            return
        player = self.run.player
        player.gold += result["gold"]
        # TODO(D): healing after a fight is a placeholder rule (the number is in data/progression.json).
        player.heal(round(player.max_hp * load_data("progression.json")["heal_after_fight"]))
        self.floor.enemies.remove(map_enemy)
        self.say(t("fight_won", enemy=self.enemy_info[map_enemy["id"]].name, xp=result["xp"], gold=result["gold"]))
        for event in player.gain_xp(result["xp"]):
            kind, value = event.split(":")
            if kind == "level_up":
                self.say(t("level_up", level=value))
            else:
                name = next(m["name"] for m in player.unlocked_moves() if m["id"] == value)
                self.say(t("new_move", name=name))
        self.refresh_hotbar()   # a level up may have unlocked a new move

    def next_floor(self):
        rules = load_data("progression.json")
        if self.run.floor_number >= rules["last_floor"]:
            from ui.screens import EndScene
            self.game.scenes.replace(EndScene(self.game, won=True))
            return
        self.run.floor_number += 1
        player = self.run.player
        # TODO(D): healing on a new floor is a placeholder rule, like the one above.
        player.heal(round(player.max_hp * rules["heal_on_new_floor"]))
        self.game.scenes.replace(DungeonScene(self.game, [t("new_floor", n=self.run.floor_number)]))

    # --- every frame -------------------------------------------------------
    def update(self, dt):
        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]
        self.camera.move_towards(*self.player_center(), dt)

    def draw(self, surface):
        characters = [(e["pos"][0], e["pos"][1], self.enemy_images[e["id"]]) for e in self.floor.enemies]
        characters.append((self.player_pos[0], self.player_pos[1], self.player_image))
        self.renderer.draw(surface, VIEW, self.camera, characters)
        self.draw_hud(surface)

    def draw_hud(self, surface):
        """Everything drawn on top of the dungeon: status panel, floor number, messages, hotbar."""
        fonts = self.game.fonts
        hud.draw_player_panel(surface, fonts, self.run.player)
        hud.draw_floor_label(surface, fonts, self.run.floor_number)
        lines = [(message, theme.GOLD) for message, _ in self.messages]
        hud.draw_messages(surface, fonts, lines, bottom=self.hotbar.rects[0].top - 20)
        self.hotbar.draw(surface, fonts, pygame.mouse.get_pos())
