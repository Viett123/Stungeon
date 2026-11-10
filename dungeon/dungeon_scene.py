"""The dungeon you walk through (owner: A).

Walk into an enemy to fight it. The boss stands on the stairs: beat it, step on the
stairs, and you go down to the next floor. Enemies don't move yet (TODO(C): A* chasing).
"""
import pygame

from core import settings
from core.scene import Scene
from core.strings import t
from dungeon.floor import STAIRS, WALL, generate_floor
from systems.enemies import make_enemy
from systems.player import load_data
from ui import widgets

MOVE_KEYS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
TOP = 48    # one tile row at the top for the status bar
LEFT = (settings.SCREEN_W - 26 * settings.TILE) // 2


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

    def next_floor(self):
        rules = load_data("progression.json")
        if self.run.floor_number >= rules["last_floor"]:
            from ui.screens import EndScene
            self.game.scenes.replace(EndScene(self.game, won=True))
            return
        self.run.floor_number += 1
        player = self.run.player
        player.heal(round(player.max_hp * rules["heal_on_new_floor"]))
        self.game.scenes.replace(DungeonScene(self.game, [t("new_floor", n=self.run.floor_number)]))

    # --- every frame -------------------------------------------------------
    def update(self, dt):
        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]

    def draw(self, surface):
        tile = settings.TILE
        for y, row in enumerate(self.floor.grid):
            for x, cell in enumerate(row):
                if cell == WALL:
                    continue
                color = settings.COLOR_STAIRS if cell == STAIRS else settings.COLOR_FLOOR
                pygame.draw.rect(surface, color, (LEFT + x * tile, TOP + y * tile, tile - 1, tile - 1))

        small = self.game.fonts["small"]
        for e in self.floor.enemies:
            info = self.enemy_info[e["id"]]
            x, y = e["pos"]
            pad = 2 if e["boss"] else 8
            rect = pygame.Rect(LEFT + x * tile + pad, TOP + y * tile + pad, tile - 2 * pad, tile - 2 * pad)
            pygame.draw.rect(surface, info.color, rect, border_radius=6)
            widgets.text(surface, small, self.letter[e["id"]], settings.COLOR_BG, rect.center, "center")

        player = self.run.player
        px, py = self.player_pos
        pygame.draw.rect(surface, player.color, (LEFT + px * tile + 8, TOP + py * tile + 8, tile - 16, tile - 16),
                         border_radius=12)

        hud = t("hud", floor=self.run.floor_number, cls=player.class_name, level=player.level,
                hp=player.hp, max_hp=player.max_hp, res=player.resource_name, r=player.resource,
                max_r=player.max_resource, xp=player.xp, gold=player.gold)
        widgets.text(surface, self.game.fonts["normal"], hud, settings.COLOR_TEXT, (24, 14))
        if self.messages:
            y = settings.SCREEN_H - 30 * len(self.messages) - 10
            for message, _ in self.messages:
                widgets.text(surface, small, message, settings.COLOR_HIGHLIGHT, (settings.SCREEN_W // 2, y), "midtop")
                y += 30
        else:
            widgets.text(surface, small, t("dungeon_hint"), settings.COLOR_DIM,
                         (settings.SCREEN_W // 2, settings.SCREEN_H - 34), "midtop")
