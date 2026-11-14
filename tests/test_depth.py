"""Fog of war, minimap, room kinds, traps, elites, mini-bosses, choices, items in fights, hit effects."""
import os
import random

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat.combat_scene import CombatScene                 # noqa: E402
from core import flow                                       # noqa: E402
from core.game import Game                                  # noqa: E402
from core.run import new_run, run_from_dict, run_to_dict    # noqa: E402
from dungeon import fog                                     # noqa: E402
from dungeon.dungeon_scene import DungeonScene              # noqa: E402
from dungeon.floor import generate_floor                    # noqa: E402
from systems import choices, inventory, save                # noqa: E402
from systems.enemies import elite_rules, floor_spawns, floor_theme, make_enemy   # noqa: E402
from systems.player import load_data                        # noqa: E402
from ui import anim                                         # noqa: E402
from ui.choice_screen import ChoiceScene                    # noqa: E402

SEEDS = range(12)


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


def room_cells(room):
    x, y, w, h = room
    return {(cx, cy) for cy in range(y, y + h) for cx in range(x, x + w)}


@pytest.fixture
def game():
    g = Game()
    yield g
    pygame.quit()


@pytest.fixture
def dungeon(game):
    flow.start_new_run(game, "warrior")
    return game, game.scenes.current


# --- room kinds, traps, elites, mini-bosses (the floor itself) ---------------
@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_have_kinds_and_special_rooms_hold_what_they_should(seed):
    floor = generate_floor(2, seed)
    kinds = floor.room_kinds
    assert kinds[0] == "start" and kinds[-1] == "boss" and len(kinds) == len(floor.rooms)
    start_room = room_cells(floor.rooms[0])
    things = [e["pos"] for e in floor.enemies] + [c["pos"] for c in floor.chests]
    assert not start_room & set(things)                       # nothing in the start room
    assert not floor.traps & set(things)                      # nothing stands on spikes
    assert len(set(things)) == len(things)                    # no two things on one cell

    if "trap" in kinds:
        trap_room = floor.rooms[kinds.index("trap")]
        center_x, center_y = trap_room[0] + trap_room[2] // 2, trap_room[1] + trap_room[3] // 2
        assert floor.traps and floor.traps <= room_cells(trap_room)
        assert all(x != center_x and y != center_y for x, y in floor.traps)   # a safe way through
    else:
        assert not floor.traps

    guards = [e for e in floor.enemies if e["guard"]]
    if "treasure" in kinds:
        treasure_room = floor.rooms[kinds.index("treasure")]
        mini = next(e for e in guards if not e["boss"])
        assert mini["id"] == floor_spawns(2)["miniboss"] and mini["pos"] in room_cells(treasure_room)
        assert sum(c["pos"] in room_cells(treasure_room) for c in floor.chests) >= 1


def test_modifiers_change_the_next_floor():
    plain = generate_floor(1, seed=5)
    richer = generate_floor(1, seed=5, modifiers={"extra_chests": 2, "extra_enemies": 3})
    assert len(richer.chests) == len(plain.chests) + 2
    assert len(richer.enemies) == len(plain.enemies) + 3
    all_elite = generate_floor(1, seed=5, modifiers={"elite_bonus": 1.0})
    assert all(e["elite"] for e in all_elite.enemies if not e["guard"])
    none_elite = generate_floor(1, seed=5, modifiers={"elite_bonus": -1.0})
    assert not any(e["elite"] for e in none_elite.enemies)


def test_an_elite_is_stronger_and_drops_from_the_elite_table():
    normal, elite = make_enemy("article_goblin"), make_enemy("article_goblin", elite=True)
    rules = elite_rules()
    assert elite.elite and elite.hp == round(normal.hp * rules["hp"]) and elite.max_hp == elite.hp
    assert elite.damage >= normal.damage and elite.xp > normal.xp
    assert elite.loot_table == rules["loot"]
    assert make_enemy(floor_spawns(1)["miniboss"]).large_art


def test_a_run_keeps_its_theme_and_only_uses_allowed_ones():
    allowed = floor_spawns(1)["theme"]
    themes = load_data("themes.json")["themes"]
    assert floor_theme(1, seed=7) == floor_theme(1, seed=7)
    assert floor_theme(1, seed=7) in [themes[name] for name in allowed]
    assert len({floor_theme(1, seed=s)["folder"] for s in range(30)}) > 1     # different runs can look different


# --- fog of war --------------------------------------------------------------
def test_standing_in_a_room_shows_the_whole_room_and_its_walls():
    floor = generate_floor(1, seed=2)
    x, y, w, h = floor.rooms[0]
    view = fog.cells_in_view(floor, floor.start)
    assert room_cells(floor.rooms[0]) <= view
    assert (x - 1, y - 1) in view and (x + w, y + h) in view     # the walls around it
    other = floor.rooms[-1]
    assert (other[0] + 1, other[1] + 1) not in view              # a far room stays hidden


def test_standing_in_a_corridor_shows_only_a_few_cells():
    floor = generate_floor(1, seed=2)
    corridor = next((x, y) for y in range(floor.height) for x in range(floor.width)
                    if floor.is_walkable(x, y) and floor.room_at(x, y) is None)
    assert len(fog.cells_in_view(floor, corridor)) <= (2 * fog.CORRIDOR_RADIUS + 1) ** 2


def test_walking_lifts_the_fog_and_hidden_monsters_are_not_on_the_minimap(dungeon):
    game, scene = dungeon
    seen_at_start = len(scene.seen)
    assert room_cells(scene.floor.rooms[0]) <= scene.seen
    hidden = [e for e in scene.floor.enemies if e["pos"] not in scene.seen]
    assert hidden                                               # most of the floor is still in the fog
    scene.floor.enemies[:] = []                                 # nobody interrupts the walk
    scene.floor.chests[:] = []
    # Put the player just inside a normal room and take one step there.
    room = scene.floor.rooms[scene.floor.room_kinds.index("normal")]
    x, y = room[0] + 1, room[1] + 1
    scene.player_pos = (x, y)
    scene.try_move(x + 1, y)
    assert scene.player_pos == (x + 1, y)
    assert len(scene.seen) > seen_at_start and room_cells(room) <= scene.seen
    scene.update(1 / 60)
    scene.draw(game.screen)                                     # fog, minimap and all


def test_spikes_hurt_and_can_end_the_run(dungeon):
    game, scene = dungeon
    scene.floor.enemies[:] = []
    scene.floor.chests[:] = []
    x, y = scene.player_pos
    scene.floor.traps.add((x + 1, y))
    player = game.run_state.player
    scene.try_move(x + 1, y)
    assert player.hp == player.max_hp - load_data("progression.json")["trap_damage"]
    player.hp = 1
    scene.try_move(x, y)
    scene.floor.traps.add((x + 1, y))
    scene.try_move(x + 1, y)
    assert not isinstance(game.scenes.current, DungeonScene)    # the end screen


def test_a_guard_never_leaves_its_spot(dungeon):
    game, scene = dungeon
    guard = next(e for e in scene.floor.enemies if e["guard"] and not e["boss"])
    scene.floor.enemies[:] = [guard]
    x, y = scene.player_pos
    guard["pos"] = (x + 2, y)
    for _ in range(180):
        scene.update(1 / 60)
    assert guard["pos"] == (x + 2, y) and game.scenes.current is scene


# --- the choice between floors -----------------------------------------------
def test_offer_gives_distinct_choices_and_the_same_ones_for_the_same_seed():
    data = load_data("choices.json")
    first = choices.offer(random.Random(3))
    assert len(first) == data["offered"] and len({c["id"] for c in first}) == len(first)
    assert [c["id"] for c in choices.offer(random.Random(3))] == [c["id"] for c in first]


def test_every_choice_can_be_applied_and_none_kills_or_heals():
    for choice in load_data("choices.json")["choices"]:
        run = new_run("mage", seed=1)
        run.player.hp = 5
        choices.apply(choice, run)
        assert 1 <= run.player.hp <= 5, choice["id"]
        if "item" in choice["effects"]:
            assert choice["effects"]["item"] in run.player.inventory
        for name, amount in choice["effects"].get("next_floor", {}).items():
            assert run.next_modifiers[name] == amount


def test_choice_screen_applies_the_pick_and_the_next_floor_uses_it(game):
    flow.start_new_run(game, "archer")
    run = game.run_state
    flow.offer_choice(game)
    screen = game.scenes.current
    assert isinstance(screen, ChoiceScene)
    screen.options = [{"id": "test", "name": "Test", "text": "Two more chests.",
                       "effects": {"gold": 7, "next_floor": {"extra_chests": 2}}}] * len(screen.options)
    screen.draw(game.screen)
    gold = run.player.gold
    screen.handle_event(key(pygame.K_RIGHT))
    screen.handle_event(key(pygame.K_RETURN))
    assert isinstance(game.scenes.current, DungeonScene) and run.floor_number == 2
    assert run.player.gold == gold + 7
    assert run.modifiers == {"extra_chests": 2} and run.next_modifiers == {}
    plain = generate_floor(2, run.seed)
    assert len(game.scenes.current.floor.chests) == len(plain.chests) + 2
    assert run_from_dict(save.load_game()).modifiers == {"extra_chests": 2}   # Continue rebuilds the same floor


def test_modifiers_survive_a_save():
    run = new_run("warrior", seed=4)
    run.modifiers = {"elite_bonus": 0.3}
    assert run_from_dict(run_to_dict(run)).modifiers == {"elite_bonus": 0.3}


# --- items and hit effects in a fight ----------------------------------------
def start_fight(game):
    flow.start_new_run(game, "warrior")
    scene = game.scenes.current
    scene.start_fight(next(e for e in scene.floor.enemies if not e["guard"]))
    fight = game.scenes.current
    assert isinstance(fight, CombatScene)
    return fight


def test_a_potion_can_be_drunk_in_a_fight_and_costs_the_turn(game):
    fight = start_fight(game)
    player = fight.player
    inventory.add_item(player, "small_potion")
    inventory.add_item(player, "small_potion")
    player.take_damage(60)
    hurt = player.hp

    fight.handle_event(key(pygame.K_i))
    assert fight.state == "items" and fight.item_ids == ["small_potion"]
    fight.draw(game.screen)
    fight.handle_event(key(pygame.K_RETURN))
    assert player.hp > hurt and player.inventory == ["small_potion"]
    assert fight.state == "message"
    healed = player.hp
    fight.handle_event(key(pygame.K_RETURN))                    # the enemy takes its turn
    assert player.hp < healed


def test_no_items_or_a_useless_item_does_not_cost_the_turn(game):
    fight = start_fight(game)
    fight.handle_event(key(pygame.K_i))
    assert fight.state == "choose" and fight.notice             # nothing to use
    inventory.add_item(fight.player, "small_potion")
    fight.handle_event(key(pygame.K_i))
    fight.handle_event(key(pygame.K_RETURN))                    # full HP: the potion would do nothing
    assert fight.state == "items" and fight.player.inventory == ["small_potion"] and fight.notice
    fight.handle_event(key(pygame.K_ESCAPE))
    assert fight.state == "choose"


def test_a_hit_shakes_flashes_and_pauses_for_a_moment(game):
    fight = start_fight(game)
    fight.pick_move(0)
    fight.submit(fight.battle.question["answer"])
    assert fight.freeze > 0 and fight.flash > 0 and fight.shake.until > anim.now()
    attack = fight.attack
    fight.update(1 / 60)                                        # during the pause nothing moves on
    assert fight.attack == attack
    for _ in range(120):
        fight.update(1 / 60)
        fight.draw(game.screen)                                 # draws through the shake and the flash
    assert fight.freeze <= 0 and fight.flash == 0


def test_shake_fades_out_and_stays_small(monkeypatch):
    clock = {"now": 10.0}
    monkeypatch.setattr(anim, "now", lambda: clock["now"])
    shake = anim.Shake()
    assert shake.offset() == (0, 0)
    shake.start(strength=8, seconds=0.5)
    clock["now"] += 0.1
    x, y = shake.offset()
    assert abs(x) <= 8 and abs(y) <= 8
    clock["now"] += 1
    assert shake.offset() == (0, 0)


# --- torches and golden chests -----------------------------------------------
def test_treasure_room_chests_are_golden_and_the_others_are_not():
    floor = generate_floor(2, seed=3)
    treasure = room_cells(floor.rooms[floor.room_kinds.index("treasure")])
    for chest in floor.chests:
        assert chest["golden"] == (chest["pos"] in treasure)


def test_torches_hang_only_on_bricks_behind_rooms(dungeon):
    from dungeon import tiles
    game, scene = dungeon
    renderer = scene.renderer
    assert renderer.torches                                  # the art exists, so some torches are placed
    for x, y in renderer.torches:
        assert tiles.is_brick(scene.floor.grid, x, y) and scene.floor.is_walkable(x, y + 1)


def test_a_golden_chest_uses_its_own_pictures_and_loot(dungeon, monkeypatch):
    import dungeon.dungeon_scene as module
    game, scene = dungeon
    asked = []
    monkeypatch.setattr(module, "roll_loot", lambda table, rng: asked.append(table) or [])
    chest = {"pos": (0, 0), "opened": False, "golden": True, "time": 0.0}
    assert scene.chest_image(chest) is scene.golden_frames[0]
    scene.open_chest(chest)
    assert asked == ["chest_golden"] and chest["opened"]
