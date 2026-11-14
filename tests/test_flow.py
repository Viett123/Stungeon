"""Saving, continuing, menus, bag and shop screens, run without a window.

tests/conftest.py makes every test save into its own temporary folder.
"""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import flow                               # noqa: E402
from core.game import Game                          # noqa: E402
from core.run import new_run, run_from_dict, run_to_dict   # noqa: E402
from core.title_scene import TitleScene             # noqa: E402
from dungeon.dungeon_scene import DungeonScene      # noqa: E402
from systems import inventory, save, shop           # noqa: E402
from systems.player import load_data                # noqa: E402
from ui.choice_screen import ChoiceScene            # noqa: E402
from ui.class_select import ClassSelectScene        # noqa: E402
from ui.inventory_screen import InventoryScene      # noqa: E402
from ui.pause_menu import PauseScene                # noqa: E402
from ui.screens import EndScene                     # noqa: E402
from ui.shop_screen import ShopScene                # noqa: E402

ITEMS = load_data("items.json")["items"]
POTION = next(i for i, item in ITEMS.items() if item.get("effect", {}).get("type") == "heal")


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


def press(game, *keys):
    """Send key presses to the current scene, then update and draw it once."""
    for k in keys:
        game.scenes.current.handle_event(key(k))
    game.scenes.current.update(1 / 60)
    game.scenes.current.draw(game.screen)


@pytest.fixture
def game():
    g = Game()
    yield g
    pygame.quit()


# --- the save data itself (no window needed) ---------------------------------
def test_run_survives_a_save_and_load():
    run = new_run("mage", seed=7)
    run.floor_number = 2
    run.player.gain_xp(60)
    run.player.resource = 0                 # a saved 0 must stay 0
    run.player.gold = 33
    inventory.add_item(run.player, POTION)
    run.engine.stats["articles"] = {"asked": 4, "correct": 3}

    loaded = run_from_dict(run_to_dict(run))
    assert loaded.floor_number == 2 and loaded.seed == 7
    for name in ("class_id", "level", "xp", "gold", "hp", "max_hp", "resource", "inventory", "equipped"):
        assert getattr(loaded.player, name) == getattr(run.player, name), name
    assert loaded.engine.stats["articles"] == {"asked": 4, "correct": 3}


def test_a_save_from_another_version_is_refused():
    data = run_to_dict(new_run("archer", seed=1))
    data["version"] = 999
    with pytest.raises(ValueError):
        run_from_dict(data)


def test_a_damaged_save_file_counts_as_no_save():
    save.SAVE_PATH.write_text("{ this is not json", encoding="utf-8")
    assert save.load_game() == {} and not save.has_save()


# --- the title menu ----------------------------------------------------------
def test_continue_is_greyed_out_without_a_save(game):
    title = game.scenes.current
    assert isinstance(title, TitleScene)
    assert [b.enabled for b in title.buttons] == [True, False, True, True, True]   # only Continue is greyed out
    press(game, pygame.K_DOWN)               # skips the greyed-out Continue
    assert title.selected == 2


def test_new_game_saves_and_continue_brings_it_back(game):
    press(game, pygame.K_RETURN)             # New game
    assert isinstance(game.scenes.current, ClassSelectScene)
    press(game, pygame.K_2, pygame.K_RETURN)  # Mage
    assert isinstance(game.scenes.current, DungeonScene) and save.has_save()
    seed = game.run_state.seed

    game.go_to_title()
    assert game.scenes.current.buttons[1].enabled
    press(game, pygame.K_DOWN, pygame.K_RETURN)   # Continue
    assert isinstance(game.scenes.current, DungeonScene)
    assert game.run_state.seed == seed and game.run_state.player.class_id == "mage"


def test_demo_starts_with_one_key_and_is_never_saved(game):
    press(game, pygame.K_F1)
    assert isinstance(game.scenes.current, DungeonScene)
    assert game.run_state.demo and not save.has_save()
    assert game.run_state.player.class_id == load_data("demo.json")["class"]


def test_winning_deletes_the_save_but_losing_keeps_the_checkpoint(game):
    flow.start_new_run(game, "warrior")
    flow.finish_run(game, won=False)
    assert isinstance(game.scenes.current, EndScene) and save.has_save()
    flow.finish_run(game, won=True)
    assert not save.has_save()


# --- pause menu and bag ------------------------------------------------------
def test_pause_menu_opens_and_closes(game):
    flow.start_new_run(game, "warrior")
    dungeon = game.scenes.current
    press(game, pygame.K_ESCAPE)
    assert isinstance(game.scenes.current, PauseScene)
    press(game, pygame.K_ESCAPE)
    assert game.scenes.current is dungeon
    press(game, pygame.K_ESCAPE, pygame.K_DOWN, pygame.K_RETURN)   # Paused -> Bag
    assert isinstance(game.scenes.current, InventoryScene)


def test_bag_uses_a_potion_and_equips_and_takes_off(game):
    flow.start_new_run(game, "warrior")
    player = game.run_state.player
    weapon = next(i for i, item in ITEMS.items() if item.get("slot") == "weapon")
    player.equipped.clear()                            # put the starting weapon away for this test
    inventory.add_item(player, POTION)
    inventory.add_item(player, weapon)
    player.take_damage(30)

    press(game, pygame.K_i)
    bag = game.scenes.current
    press(game, pygame.K_RETURN)                       # use the potion in slot 1
    assert player.inventory == [weapon] and player.hp > player.max_hp - 30
    press(game, pygame.K_RETURN)                       # the weapon moved to slot 1: equip it
    assert player.equipped == {"weapon": weapon} and player.inventory == []
    bag.selected = bag.size                            # the weapon slot
    press(game, pygame.K_RETURN)                       # take it off
    assert player.equipped == {} and player.inventory == [weapon]
    press(game, pygame.K_i)                            # close
    assert isinstance(game.scenes.current, DungeonScene)


# --- shop --------------------------------------------------------------------
def test_shop_sells_an_item_then_leads_to_the_next_floor(game):
    flow.start_new_run(game, "archer")
    player = game.run_state.player
    first = shop.stock(1)[0]
    player.gold = ITEMS[first]["price"]

    flow.leave_floor(game)                             # as if the player stepped on the stairs
    assert isinstance(game.scenes.current, ShopScene)
    press(game, pygame.K_RETURN)                       # buy the first item
    assert player.inventory == [first] and player.gold == 0
    press(game, pygame.K_RETURN)                       # no gold left: nothing happens
    assert player.inventory == [first]

    press(game, pygame.K_c)
    assert isinstance(game.scenes.current, ChoiceScene)      # the risk-and-reward choice comes next
    press(game, pygame.K_RETURN)
    assert isinstance(game.scenes.current, DungeonScene) and game.run_state.floor_number == 2
    assert save.load_game()["floor_number"] == 2       # the new floor was saved


def test_the_last_floor_ends_the_run_instead_of_opening_a_shop(game):
    flow.start_new_run(game, "archer")
    game.run_state.floor_number = load_data("progression.json")["last_floor"]
    flow.leave_floor(game)
    assert isinstance(game.scenes.current, EndScene) and game.scenes.current.won


def test_only_items_heal_the_player(game):
    """Team rule: no healing after a fight, on a new floor or on a level up."""
    flow.start_new_run(game, "warrior")
    player = game.run_state.player
    player.take_damage(50)
    hurt = player.hp

    dungeon = game.scenes.current
    enemy = next(e for e in dungeon.floor.enemies if not e["boss"])
    dungeon.after_fight(enemy, {"won": True, "fled": False, "xp": 500, "gold": 1, "loot": []})
    assert player.level > 1 and player.hp == hurt        # several level ups, still no healing

    flow.go_to_next_floor(game)
    assert player.hp == hurt

    inventory.add_item(player, POTION)
    assert inventory.use_item(player, POTION) and player.hp > hurt
