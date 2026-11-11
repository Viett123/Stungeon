"""Equipment slots, item descriptions, the Progress screen and the answer streak."""
import os
import random

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat import effects                              # noqa: E402
from combat.battle import Battle                        # noqa: E402
from core import flow                                   # noqa: E402
from core.game import Game                              # noqa: E402
from core.run import new_run, run_to_dict               # noqa: E402
from questions.engine import QuestionEngine             # noqa: E402
from systems import inventory, items, save              # noqa: E402
from systems.enemies import make_enemy                  # noqa: E402
from systems.player import Player, load_data            # noqa: E402
from ui import item_info, topic_names                   # noqa: E402
from ui.inventory_screen import InventoryScene          # noqa: E402
from ui.stats_screen import StatsScene, mastery_color, xp_progress   # noqa: E402

ALL = load_data("items.json")["items"]


def first_item(slot):
    return next(item_id for item_id, item in ALL.items() if item.get("slot") == slot)


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


@pytest.fixture
def game():
    g = Game()
    yield g
    pygame.quit()


# --- the data ----------------------------------------------------------------
def test_every_equipment_item_names_a_known_slot_and_every_item_has_a_description():
    for item_id, item in ALL.items():
        assert item["text"], item_id
        if item["kind"] == "equipment":
            assert item["slot"] in inventory.SLOT_KINDS, item_id


def test_there_is_something_to_wear_in_every_slot():
    for kind in inventory.SLOT_KINDS:
        assert first_item(kind)


# --- the rules ---------------------------------------------------------------
def test_each_piece_goes_into_its_own_slot():
    player = Player("warrior")
    for kind in ("weapon", "head", "body", "legs", "shoes"):
        item_id = first_item(kind)
        inventory.add_item(player, item_id)
        assert inventory.equip(player, item_id)
        assert player.equipped[kind] == item_id
    assert player.inventory == []


def test_two_accessories_fill_both_slots_and_a_third_replaces_the_first():
    player = Player("mage")
    ring = first_item("accessory")
    for _ in range(3):
        inventory.add_item(player, ring)
        inventory.equip(player, ring)
    assert player.equipped == {"accessory_1": ring, "accessory_2": ring}
    assert player.inventory == [ring]            # the replaced one came back into the bag


def test_any_slot_can_be_emptied_again():
    player = Player("archer")
    for kind in inventory.SLOT_KINDS:
        inventory.add_item(player, first_item(kind))
        inventory.equip(player, first_item(kind))
    for slot in list(player.equipped):
        assert inventory.unequip(player, slot)
    assert player.equipped == {} and len(player.inventory) == len(inventory.SLOT_KINDS)


# --- descriptions ------------------------------------------------------------
def test_item_lines_give_name_kind_and_description():
    hood = items.get_item(first_item("head"))
    (name, _), (kind, _), (text, _) = item_info.item_lines(hood)
    assert name == hood["name"] and "Head" in kind and text == hood["text"]
    potion = items.get_item("small_potion")
    assert "Consumable" in item_info.item_lines(potion)[1][0]


# --- the bag screen ----------------------------------------------------------
def test_bag_screen_shows_seven_slots_and_x_takes_the_weapon_off(game):
    flow.start_new_run(game, "warrior")
    player = game.run_state.player
    weapon = player.equipped["weapon"]
    game.scenes.push(InventoryScene(game))
    bag = game.scenes.current
    assert len(bag.equip_rects) == 7

    bag.handle_event(key(pygame.K_TAB))                  # jump to the equipment slots (weapon first)
    assert bag.on_equipment() and bag.selected_item()["id"] == weapon
    bag.handle_event(key(pygame.K_x))
    assert player.equipped == {} and player.inventory == [weapon]
    bag.draw(game.screen)

    bag.handle_event(key(pygame.K_TAB))                  # back to the bag
    bag.handle_event(key(pygame.K_RETURN))               # equip it again
    assert player.equipped == {"weapon": weapon}


def test_up_and_down_stay_inside_the_equipment_grid(game):
    flow.start_new_run(game, "mage")
    game.scenes.push(InventoryScene(game))
    bag = game.scenes.current
    bag.handle_event(key(pygame.K_TAB))
    bag.handle_event(key(pygame.K_DOWN))
    assert bag.selected == bag.size + 4                  # second row of equipment
    bag.handle_event(key(pygame.K_DOWN))
    assert bag.selected == bag.size + 4                  # no third row: stays


# --- saves -------------------------------------------------------------------
def test_an_old_save_is_not_offered_for_continue(game):
    data = run_to_dict(new_run("mage", seed=3))
    save.save_game(data)
    assert flow.can_continue()
    data["version"] = 1                                  # a save from an older version of the game
    save.save_game(data)
    assert not flow.can_continue()
    game.go_to_title()
    assert not game.scenes.current.buttons[1].enabled    # Continue is greyed out


# --- progress screen ---------------------------------------------------------
def test_xp_progress_counts_inside_the_current_level():
    table = load_data("progression.json")
    player = Player("warrior")
    player.gain_xp(table["xp_for_level"]["2"] + 5)
    gained, needed = xp_progress(player)
    assert gained == 5 and needed == table["xp_for_level"]["3"] - table["xp_for_level"]["2"]
    assert xp_progress(Player("warrior", level=table["max_level"])) is None


def test_mastery_colour_goes_from_bad_to_good():
    assert mastery_color(0.1) != mastery_color(0.5) != mastery_color(0.9)


def test_progress_screen_lists_only_topics_of_the_floors_reached(game):
    flow.start_new_run(game, "archer")
    run = game.run_state
    question = run.engine.next_question(1, "easy")
    run.engine.report_answer(question, True, 3)
    game.scenes.current.handle_event(key(pygame.K_m))
    screen = game.scenes.current
    assert isinstance(screen, StatsScene)
    shown = {name for name, _, _ in screen.rows}
    assert shown == {topic_names.label(q["topic"]) for q in run.engine.questions if q["einheit"] == 1}
    asked_name, _, counts = screen.rows[0]                # asked topics come first
    assert asked_name == topic_names.label(question["topic"])
    assert counts["correct"] == 1 and screen.streak == 1
    assert screen.asked == 1 and screen.correct == 1
    screen.draw(game.screen)
    screen.handle_event(key(pygame.K_m))
    assert not isinstance(game.scenes.current, StatsScene)


# --- streak and the new combat hook ------------------------------------------
def test_streak_counts_right_answers_in_a_row():
    engine = QuestionEngine(rng=random.Random(4))
    question = engine.next_question(1, "easy")
    for correct, expected in ((True, 1), (True, 2), (False, 0), (True, 1)):
        engine.report_answer(question, correct, 2)
        assert engine.streak == expected


def test_battle_remembers_answer_times_and_the_enemy_can_be_made_to_skip_its_turn(monkeypatch):
    player = Player("warrior")
    battle = Battle(player, make_enemy("article_goblin"), QuestionEngine(rng=random.Random(5)), floor=1)
    battle.choose_move(battle.moves()[0]["id"])
    battle.answer("definitely wrong", seconds=7.5)
    assert battle.seconds == [7.5]
    monkeypatch.setattr(effects, "enemy_loses_turn", lambda b: True)
    assert battle.enemy_turn() == {"damage": 0, "taunt": None}
    assert player.hp == player.max_hp
