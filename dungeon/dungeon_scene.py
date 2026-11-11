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
from dungeon import chase, fog, sprites
from dungeon.actor import make_actor
from dungeon.camera import Camera
from dungeon.floor import STAIRS, generate_floor
from dungeon.renderer import DungeonRenderer
from dungeon.weapon import held_weapon
from systems import inventory, items
from systems.enemies import chase_rules, floor_theme, make_enemy
from systems.loot import roll_chest_gold, roll_loot
from systems.player import load_data
from ui import hud, move_info, theme
from ui.hotbar import Hotbar
from ui.minimap import Minimap

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
        self.floor = generate_floor(self.run.floor_number, seed=self.run.seed, demo=self.run.demo,
                                    modifiers=self.run.modifiers)
        self.player_pos = self.floor.start
        self.chase = chase_rules()
        # Enemy data (names, colours) loaded once here, not in draw().
        self.enemy_info = {e["id"]: make_enemy(e["id"]) for e in self.floor.enemies}
        self.seen = set()           # cells the player has seen (fog of war)
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
        theme = floor_theme(self.run.floor_number, self.run.seed)
        self.renderer = DungeonRenderer(self.floor, theme["folder"], theme["background"])
        self.camera = Camera(VIEW.width, VIEW.height, self.renderer.world_w, self.renderer.world_h)
        font = self.game.fonts["small"]
        player = self.run.player
        self.player_actor = make_actor(f"player_{player.class_id}", self.player_pos, player.color)
        self.camera.snap_to(*self.player_actor.center())
        self.weapon_id = None       # which weapon the picture below shows
        self.weapon = None
        self.refresh_weapon()
        enemy_speed = TILE / self.chase["seconds_per_step"]   # the glide takes exactly one step
        for e in self.floor.enemies:
            info = self.enemy_info[e["id"]]
            # Map letter: first letter of the name, skipping "The" (only used without art).
            letter = next(word for word in info.name.split() if word != "The")[0]
            e["actor"] = make_actor(f"enemy_{e['id']}", e["pos"], info.color, letter, font,
                                    big=info.boss and not info.large_art, speed=enemy_speed)
            e.update(awake=False, timer=0.0, rest=0.0)
        self.aura = sprites.elite_aura()
        self.minimap = Minimap(self.floor, (settings.SCREEN_W - 12, 74))
        self.look_around()
        self.chest_frames = sprites.chest_frames()
        for chest in self.floor.chests:
            chest["time"] = 0.0     # seconds since it was opened, for the opening animation

    def look_around(self):
        """Fog of war: mark what the player sees from here and lift the fog from new cells."""
        new_cells = fog.cells_in_view(self.floor, self.player_pos) - self.seen
        if new_cells:
            self.seen |= new_cells
            self.renderer.reveal(new_cells)
            self.minimap.reveal(new_cells)

    def refresh_weapon(self):
        """Make the picture of the equipped weapon again if the player changed it in the bag."""
        equipped = self.run.player.equipped.get("weapon")
        if equipped != self.weapon_id:
            self.weapon_id = equipped
            self.weapon = held_weapon(self.run.player, settings.TILE_SCALE)

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
        elif event.key == pygame.K_m:
            from ui.stats_screen import StatsScene
            self.game.scenes.push(StatsScene(self.game))
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
        self.look_around()
        if (x, y) in self.floor.traps and self.step_on_spikes():
            return
        if self.floor.grid[y][x] == STAIRS:
            flow.leave_floor(self.game)   # shop, next floor or the end screen: see core/flow.py

    def step_on_spikes(self):
        """Spikes hurt. Returns True if they ended the run."""
        # TODO(D): the trap damage is a placeholder number in data/progression.json.
        damage = self.run.player.take_damage(load_data("progression.json")["trap_damage"])
        self.say(t("trap_hit", damage=damage))
        if not self.run.player.alive:
            flow.finish_run(self.game, won=False)
            return True
        return False

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
            if e["guard"]:
                continue                       # bosses and mini-bosses guard their spot and never leave it
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

        enemy = make_enemy(map_enemy["id"], elite=map_enemy["elite"])
        self.game.scenes.push(CombatScene(self.game, self.run.player, enemy, on_end))

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
        name = self.enemy_info[map_enemy["id"]].name
        if map_enemy["elite"]:
            name = t("elite_name", name=name)
        self.say(t("fight_won", enemy=name, xp=result["xp"], gold=result["gold"]))
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
        self.refresh_weapon()
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
        things = []
        for e in self.floor.enemies:
            if e["pos"] not in self.seen:
                continue                        # still hidden in the fog
            feet_x, feet_y = e["actor"].feet()
            if e["elite"]:
                things.append((feet_x, feet_y - 1, self.aura, -10))   # a gold ring on the floor under it
            things.append((feet_x, feet_y, e["actor"].image()))
        for chest in self.floor.chests:
            x, y = chest["pos"]
            if chest["pos"] not in self.seen:
                continue
            # A little higher than a character on the same tile, so the player is drawn over an open chest.
            things.append((x * TILE + TILE // 2, (y + 1) * TILE - 1, self.chest_image(chest)))
        things.append((*self.player_actor.feet(), self.player_actor.image()))
        if self.weapon:
            things.append(self.weapon.thing(*self.player_actor.feet(), self.player_actor.facing_left))
        self.renderer.draw(surface, VIEW, self.camera, things)
        self.draw_hud(surface)

    def draw_hud(self, surface):
        """Everything drawn on top of the dungeon: status panel, floor number, messages, hotbar."""
        fonts = self.game.fonts
        hud.draw_player_panel(surface, fonts, self.run.player)
        hud.draw_floor_label(surface, fonts, self.run.floor_number)
        lines = [(message, theme.GOLD) for message, _ in self.messages]
        hud.draw_messages(surface, fonts, lines, bottom=self.hotbar.rects[0].top - 20)
        self.minimap.draw(surface, self.seen, self.player_pos)
        self.hotbar.draw(surface, fonts, pygame.mouse.get_pos())
