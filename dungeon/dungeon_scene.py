"""The dungeon you walk through (owner: A).

Walk into an enemy to fight it, or let it catch you: a monster that sees you within
a few tiles runs after you and attacks when it reaches you. Walk into a chest to open
it. The boss stands on the stairs and does not chase: beat it and step on the stairs.

The rules (who is on which tile) change at once. The pictures (Actors) glide after them.
"""
import pygame

from core import flow, settings
from core.scene import Scene
from core.strings import t
from dungeon import chase, sprites
from dungeon.actor import make_actor
from dungeon.camera import Camera
from dungeon.floor import STAIRS, generate_floor
from dungeon.renderer import DungeonRenderer
from systems import inventory, items
from systems.enemies import chase_rules, make_enemy
from systems.loot import roll_chest_gold, roll_loot
from ui import hud, move_info, theme
from ui.hotbar import Hotbar

MOVE_KEYS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
TILE = settings.TILE
# The dungeon fills the whole window. The status panel and hotbar are drawn on top of it.
VIEW = pygame.Rect(0, 0, settings.SCREEN_W, settings.SCREEN_H)
HOLD_DELAY = 0.22          # seconds a key must be held before the player keeps walking
CHEST_FRAME_SECONDS = 0.1


class DungeonScene(Scene):
    def __init__(self, game, messages=None):
        super().__init__(game)
        self.run = game.run_state
        self.floor = generate_floor(self.run.floor_number, seed=self.run.seed, demo=self.run.demo)
        self.player_pos = self.floor.start
        self.chase = chase_rules()
        # Enemy data (names, colours) loaded once here, not in draw().
        self.enemy_info = {e["id"]: make_enemy(e["id"]) for e in self.floor.enemies}
        self.messages = []          # [[text, seconds left]]
        for m in messages or []:
            self.say(m)
        if self.run.floor_number == 1:
            self.say(t("dungeon_hint"))   # explain the controls once, at the start of a run
        self.held = 0.0             # how long a move key has been held down

        self.make_pictures()
        self.hotbar = Hotbar()
        self.refresh_hotbar()

    def make_pictures(self):
        """Build everything that is drawn, once, so draw() never loads a file."""
        self.renderer = DungeonRenderer(self.floor)
        self.camera = Camera(VIEW.width, VIEW.height, self.renderer.world_w, self.renderer.world_h)
        font = self.game.fonts["small"]
        player = self.run.player
        self.player_actor = make_actor(f"player_{player.class_id}", self.player_pos, player.color)
        self.camera.snap_to(*self.player_actor.center())
        enemy_speed = TILE / self.chase["seconds_per_step"]   # the glide takes exactly one step
        for e in self.floor.enemies:
            info = self.enemy_info[e["id"]]
            # Map letter: first letter of the name, skipping "The" (only used without art).
            letter = next(word for word in info.name.split() if word != "The")[0]
            e["actor"] = make_actor(f"enemy_{e['id']}", e["pos"], info.color, letter, font,
                                    big=info.boss, speed=enemy_speed)
            e.update(awake=False, timer=0.0, rest=0.0)
        self.chest_frames = sprites.chest_frames()
        for chest in self.floor.chests:
            chest["time"] = 0.0     # seconds since it was opened, for the opening animation

    def refresh_hotbar(self):
        """Show the player's moves in the hotbar. Called at the start and after a level up."""
        player = self.run.player
        entries = move_info.hotbar_entries(player.unlocked_moves(), player.resource_name, self.game.fonts["small"])
        self.hotbar.set_entries(entries)

    def say(self, message):
        self.messages.append([message, settings.MESSAGE_SECONDS])
        self.messages = self.messages[-3:]

    # --- input -------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            from ui.pause_menu import PauseScene
            self.game.scenes.push(PauseScene(self.game))
        elif event.key == pygame.K_i:
            from ui.inventory_screen import InventoryScene
            self.game.scenes.push(InventoryScene(self.game))
        elif event.key in MOVE_KEYS:
            self.held = 0.0
            self.step(*MOVE_KEYS[event.key])

    def step(self, dx, dy):
        self.try_move(self.player_pos[0] + dx, self.player_pos[1] + dy)

    def walk_while_key_held(self, dt):
        """Holding a move key keeps the player walking, one tile each time the last glide ends."""
        pressed = pygame.key.get_pressed()
        direction = next((d for key, d in MOVE_KEYS.items() if pressed[key]), None)
        if direction is None:
            self.held = 0.0
            return
        self.held += dt
        if self.held >= HOLD_DELAY and not self.player_actor.moving:
            self.step(*direction)

    def enemy_at(self, pos):
        return next((e for e in self.floor.enemies if e["pos"] == pos), None)

    def chest_at(self, pos):
        return next((c for c in self.floor.chests if c["pos"] == pos), None)

    def try_move(self, x, y):
        if not self.floor.is_walkable(x, y):
            return
        self.player_actor.face((x, y))
        enemy = self.enemy_at((x, y))
        if enemy:
            self.start_fight(enemy)
            return
        chest = self.chest_at((x, y))
        if chest and not chest["opened"]:
            self.open_chest(chest)     # the first bump opens it; after that you can walk over it
            return
        self.player_pos = (x, y)
        self.player_actor.move_to((x, y))
        if self.floor.grid[y][x] == STAIRS:
            flow.leave_floor(self.game)   # shop, next floor or the end screen: see core/flow.py

    # --- chests ------------------------------------------------------------
    def open_chest(self, chest):
        chest["opened"] = True
        player = self.run.player
        gold = roll_chest_gold(self.run.rng)
        player.gold += gold
        self.say(t("chest_gold", gold=gold))
        self.give_items(roll_loot("chest", self.run.rng))

    def give_items(self, item_ids):
        for item_id in item_ids:
            name = items.get_item(item_id)["name"]
            added = inventory.add_item(self.run.player, item_id)
            self.say(t("loot_found", item=name) if added else t("loot_bag_full", item=name))

    # --- monsters ----------------------------------------------------------
    def update_enemies(self, dt):
        """Wake monsters near the player and let awake ones walk towards the player."""
        for e in self.floor.enemies:
            e["actor"].update(dt)
        for e in self.floor.enemies:
            if e["boss"]:
                continue                       # the boss guards the stairs and never leaves them
            if e["rest"] > 0:
                e["rest"] -= dt                # standing still after the player ran away
                continue
            gap = chase.distance(e["pos"], self.player_pos)
            if gap <= self.chase["wake_radius"]:
                e["awake"] = True
            elif gap > self.chase["sleep_radius"]:
                e["awake"] = False
            if not e["awake"]:
                continue
            e["timer"] += dt
            if e["timer"] < self.chase["seconds_per_step"]:
                continue
            e["timer"] = 0.0
            if self.enemy_step(e):
                return                         # a fight started: stop for this frame

    def enemy_step(self, e):
        """Move one monster one tile. Returns True if it reached the player and a fight started."""
        blocked = {other["pos"] for other in self.floor.enemies if other is not e}
        blocked |= {c["pos"] for c in self.floor.chests if not c["opened"]}
        target = chase.next_step(self.floor, e["pos"], self.player_pos, blocked)
        if target == self.player_pos:
            e["actor"].face(self.player_pos)
            self.start_fight(e)
            return True
        if target is not None:
            e["pos"] = target
            e["actor"].move_to(target)
        return False

    # --- fights ------------------------------------------------------------
    def start_fight(self, map_enemy):
        from combat.combat_scene import CombatScene

        def on_end(result):
            self.after_fight(map_enemy, result)

        self.game.scenes.push(CombatScene(self.game, self.run.player, make_enemy(map_enemy["id"]), on_end))

    def after_fight(self, map_enemy, result):
        if result["fled"]:
            map_enemy.update(rest=self.chase["rest_after_flee"], awake=False, timer=0.0)
            self.say(t("fled"))
            return
        if not result["won"]:
            flow.finish_run(self.game, won=False)
            return
        player = self.run.player
        player.gold += result["gold"]
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
        self.give_items(result["loot"])

    # --- every frame -------------------------------------------------------
    def update(self, dt):
        for m in self.messages:
            m[1] -= dt
        self.messages = [m for m in self.messages if m[1] > 0]
        for chest in self.floor.chests:
            if chest["opened"]:
                chest["time"] += dt
        self.walk_while_key_held(dt)
        if self.game.scenes.current is not self:
            return                              # the step above opened another screen
        self.player_actor.update(dt)
        self.camera.move_towards(*self.player_actor.center(), dt)
        self.update_enemies(dt)

    def chest_image(self, chest):
        if not chest["opened"]:
            return self.chest_frames[0]
        frame = min(int(chest["time"] / CHEST_FRAME_SECONDS) + 1, len(self.chest_frames) - 1)
        return self.chest_frames[frame]

    def draw(self, surface):
        things = [(*e["actor"].feet(), e["actor"].image()) for e in self.floor.enemies]
        for chest in self.floor.chests:
            x, y = chest["pos"]
            # A little higher than a character on the same tile, so the player is drawn over an open chest.
            things.append((x * TILE + TILE // 2, (y + 1) * TILE - 1, self.chest_image(chest)))
        things.append((*self.player_actor.feet(), self.player_actor.image()))
        self.renderer.draw(surface, VIEW, self.camera, things)
        self.draw_hud(surface)

    def draw_hud(self, surface):
        """Everything drawn on top of the dungeon: status panel, floor number, messages, hotbar."""
        fonts = self.game.fonts
        hud.draw_player_panel(surface, fonts, self.run.player)
        hud.draw_floor_label(surface, fonts, self.run.floor_number)
        lines = [(message, theme.GOLD) for message, _ in self.messages]
        hud.draw_messages(surface, fonts, lines, bottom=self.hotbar.rects[0].top - 20)
        self.hotbar.draw(surface, fonts, pygame.mouse.get_pos())
