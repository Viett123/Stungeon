"""Tests for the play-test updates: drawn logo, room variety, wandering merchant, selling,
throwing items away, the streak display and music per floor look and in the boss room."""
import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import assets, flow, title_scene  # noqa: E402
from core.game import Game  # noqa: E402
from core.strings import t  # noqa: E402
from dungeon import floor as floor_module  # noqa: E402
from dungeon.dungeon_scene import BOSS_ROOM_MUSIC, DungeonScene  # noqa: E402
from dungeon.floor import WALL, generate_floor  # noqa: E402
from systems import inventory, items, shop  # noqa: E402
from systems.player import load_data  # noqa: E402
from ui import hud  # noqa: E402
from ui.inventory_screen import InventoryScene  # noqa: E402
from ui.merchant import Merchant  # noqa: E402
from ui.shop_screen import ShopScene  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEEDS = range(40)


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


@pytest.fixture
def game():
    game = Game()
    flow.start_new_run(game, "warrior")
    return game


def room_cells(room):
    x, y, w, h = room
    return {(col, row) for row in range(y, y + h) for col in range(x, x + w)}


# --- the logo -------------------------------------------------------------------
def test_without_logo_png_the_logo_is_made_in_code(monkeypatch, tmp_path):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)          # an empty folder: no logo.png
    assets.clear_cache()
    assert title_scene._drawn_logo() is None
    assets.clear_cache()


@pytest.mark.parametrize("size", [(200, 50), (60, 20), (2000, 300), (1504, 560)])
def test_a_drawn_logo_is_scaled_to_fit_above_the_menu(monkeypatch, tmp_path, size):
    Game()                                                        # a display, so images can be converted
    pygame.image.save(pygame.Surface(size), str(tmp_path / "logo.png"))
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    assets.clear_cache()
    logo = title_scene._drawn_logo()
    width, height = logo.get_size()
    assert width <= title_scene.LOGO_MAX[0] and height <= title_scene.LOGO_MAX[1]
    if size[0] <= title_scene.LOGO_MAX[0]:
        assert width % size[0] == 0                               # a whole number bigger: sharp pixels
    else:
        assert size[0] // width == size[0] / width or size[0] % width < size[0] // width   # a whole number smaller
    assets.clear_cache()


# --- rooms ----------------------------------------------------------------------
def test_floors_have_the_new_room_kinds():
    kinds = set()
    for seed in SEEDS:
        kinds |= set(generate_floor(1, seed).room_kinds)
    assert {"pillars", "storeroom", "merchant"} <= kinds


def test_monsters_are_spread_over_the_normal_and_pillar_rooms():
    for seed in SEEDS:
        floor = generate_floor(2, seed)
        monsters = len([e for e in floor.enemies if not e["guard"]])
        rooms = [i for i, kind in enumerate(floor.room_kinds) if kind in ("normal", "pillars")]
        if monsters < len(rooms) + 3:       # not enough monsters to give every room one: skip this seed
            continue
        for i in rooms:
            cells = room_cells(floor.rooms[i])
            assert any(e["pos"] in cells for e in floor.enemies), (seed, floor.room_kinds[i])


def test_storerooms_and_the_merchant_room_are_peaceful():
    for seed in SEEDS:
        floor = generate_floor(1, seed)
        for room, kind in zip(floor.rooms, floor.room_kinds):
            cells = room_cells(room)
            if kind in ("storeroom", "merchant"):
                assert not any(e["pos"] in cells for e in floor.enemies), (seed, kind)
            if kind == "storeroom":
                assert any(c["pos"] in cells for c in floor.chests), seed
            if kind == "merchant":
                assert floor.merchant in cells and not any(c["pos"] in cells for c in floor.chests)


def test_pillar_halls_have_pillars_inside():
    found = 0
    for seed in SEEDS:
        floor = generate_floor(1, seed)
        for room, kind in zip(floor.rooms, floor.room_kinds):
            x, y, w, h = room
            if kind == "pillars" and min(w, h) >= load_data("rooms.json")["pillar_min_size"]:
                inner = [(c, r) for r in range(y + 1, y + h - 1) for c in range(x + 1, x + w - 1)]
                assert any(floor.grid[r][c] == WALL for c, r in inner)
                found += 1
    assert found


def test_the_merchant_chance_comes_from_data(monkeypatch):
    rules = dict(load_data("rooms.json"), merchant_chance=0.0)
    monkeypatch.setattr(floor_module, "load_data", lambda name: rules)
    assert all(generate_floor(1, seed).merchant is None for seed in SEEDS)


def test_nobody_walks_through_the_merchant():
    floor = next(f for f in (generate_floor(1, s) for s in SEEDS) if f.merchant)
    assert not floor.is_walkable(*floor.merchant)


# --- the wandering merchant -------------------------------------------------------
def scene_with_merchant(game):
    """The dungeon of a run whose first floor has a merchant."""
    for seed in SEEDS:
        game.run_state = flow.new_run("warrior", seed=seed)
        scene = DungeonScene(game)
        if scene.floor.merchant:
            game.scenes.replace(scene)
            return scene
    raise AssertionError("no seed with a merchant on floor 1")


def test_bumping_into_the_merchant_opens_his_shop_and_esc_comes_back(game):
    scene = scene_with_merchant(game)
    x, y = scene.floor.merchant
    scene.player_pos = (x - 1, y)
    scene.try_move(x, y)
    shop_scene = game.scenes.current
    assert isinstance(shop_scene, ShopScene) and shop_scene.wandering
    assert [item["id"] for item, _ in shop_scene.entries] == shop.wandering_stock(1, game.run_state.seed)
    shop_scene.draw(game.screen)                                   # the dungeon is drawn darkened behind
    shop_scene.handle_event(key(pygame.K_ESCAPE))
    assert game.scenes.current is scene


def test_the_merchant_is_greeted_once(game):
    scene = scene_with_merchant(game)
    scene.seen.add(scene.floor.merchant)
    scene.greet_merchant()
    scene.greet_merchant()
    assert [m for m, _ in scene.messages].count(t("merchant_hello")) == 1


# --- selling ----------------------------------------------------------------------
def test_tab_switches_to_selling_and_selling_gives_gold(game):
    player = game.run_state.player
    player.inventory[:] = ["small_potion", "small_potion", "cloth_hood"]
    player.gold = 0
    scene = ShopScene(game)
    scene.handle_event(key(pygame.K_TAB))
    assert scene.mode == "sell"
    assert [(item["id"], n) for item, n in scene.entries] == [("small_potion", 2), ("cloth_hood", 1)]
    scene.handle_event(key(pygame.K_RETURN))
    assert player.inventory == ["small_potion", "cloth_hood"]
    assert player.gold == shop.sell_price(items.get_item("small_potion"))
    scene.draw(game.screen)


def test_worn_equipment_is_not_for_sale(game):
    player = game.run_state.player
    player.inventory[:] = []
    scene = ShopScene(game)
    scene.switch_mode()
    assert scene.entries == []                                     # the starting weapon is worn, not in the bag
    scene.handle_event(key(pygame.K_RETURN))                       # nothing to sell: no crash
    scene.draw(game.screen)


def test_a_long_list_scrolls_with_the_selection(game):
    player = game.run_state.player
    ids = [i for i, item in load_data("items.json")["items"].items()][:12]
    player.inventory[:] = ids
    scene = ShopScene(game)
    scene.switch_mode()
    for _ in range(len(ids) - 1):
        scene.handle_event(key(pygame.K_DOWN))
    assert scene.top <= scene.selected < scene.top + len(scene.rows)
    scene.draw(game.screen)


# --- throwing items away ----------------------------------------------------------
def test_delete_twice_throws_an_item_away(game):
    player = game.run_state.player
    player.inventory[:] = ["small_potion", "tonic"]
    scene = InventoryScene(game)
    scene.handle_event(key(pygame.K_DELETE))
    assert player.inventory == ["small_potion", "tonic"]           # the first press only asks
    assert scene.message == t("inv_drop_ask", item=items.get_item("small_potion")["name"])
    scene.handle_event(key(pygame.K_DELETE))
    assert player.inventory == ["tonic"]


def test_another_key_cancels_throwing_away(game):
    player = game.run_state.player
    player.inventory[:] = ["small_potion"]
    scene = InventoryScene(game)
    scene.handle_event(key(pygame.K_DELETE))
    scene.handle_event(key(pygame.K_RIGHT))
    scene.handle_event(key(pygame.K_LEFT))
    scene.handle_event(key(pygame.K_DELETE))                       # asks again, does not throw away
    assert player.inventory == ["small_potion"]


def test_delete_on_a_worn_item_takes_it_off(game):
    player = game.run_state.player
    player.inventory[:] = []
    scene = InventoryScene(game)
    scene.switch_side()                                            # the weapon slot
    scene.handle_event(key(pygame.K_DELETE))
    assert "weapon" not in player.equipped and len(player.inventory) == 1


# --- streak -------------------------------------------------------------------------
def test_streak_bonus_and_boxes_follow_the_numbers_in_data():
    rule = load_data("combat.json")["streak"]
    assert hud.streak_bonus(0) == 0
    assert hud.streak_bonus(1) == round(rule["bonus_per_right"] * 100)
    assert hud.streak_bonus(99) == round((rule["max_multiplier"] - 1) * 100)
    assert hud.streak_boxes() == round((rule["max_multiplier"] - 1) / rule["bonus_per_right"])


@pytest.mark.parametrize("streak", [0, 1, 3, 12])
def test_the_streak_is_drawn_on_the_map(game, streak):
    game.run_state.engine.streak = streak
    scene = game.scenes.current
    scene.draw(game.screen)


# --- music ----------------------------------------------------------------------------
def test_each_floor_look_has_its_own_music_and_the_files_exist():
    themes = json.loads((ROOT / "data" / "themes.json").read_text(encoding="utf-8"))["themes"]
    music = json.loads((ROOT / "data" / "sounds.json").read_text(encoding="utf-8"))["music"]
    names = [theme["music"] for theme in themes.values()] + [BOSS_ROOM_MUSIC]
    assert len(set(names)) == len(names)                           # all different
    for name in names:
        assert name in music and (ROOT / "assets" / "sounds" / f"music_{name}.wav").exists(), name


def test_the_boss_room_plays_its_own_music(game):
    scene = game.scenes.current
    assert scene.music == scene.theme_music
    scene.player_pos = scene.floor.rooms[-1][:2]                   # the corner of the boss room
    assert scene.music == BOSS_ROOM_MUSIC


# --- the merchant's animation ---------------------------------------------------------
def test_the_merchant_breathes_and_hops(game, monkeypatch):
    from ui import anim
    merchant = Merchant(6)
    merchant.frames = []                                           # the still picture: breathing made in code
    clock = {"now": 0.0}
    monkeypatch.setattr(anim, "now", lambda: clock["now"])
    _, low = merchant.frame()
    clock["now"] = 0.6                                             # a quarter breath later
    image, high = merchant.frame()
    assert high > low
    merchant.react()
    clock["now"] += 0.17                                           # the middle of the hop
    _, hop = merchant.frame()
    assert hop > high


# --- the wandering merchant's random stock ----------------------------------------------
def test_the_merchant_sells_a_random_mix_that_stays_the_same_in_one_run():
    rules = load_data("shop.json")["wandering"]
    stocks = {tuple(shop.wandering_stock(2, seed)) for seed in range(30)}
    assert len(stocks) > 5                                          # different runs, different items
    for stock in stocks:
        assert len(stock) == len(set(stock)) == len(rules["always"]) + rules["items"]
        assert all(item_id in stock for item_id in rules["always"])
    assert shop.wandering_stock(2, 7) == shop.wandering_stock(2, 7)   # come back: the same items


def test_the_merchant_only_picks_rarities_allowed_on_that_floor():
    allowed = load_data("shop.json")["wandering"]["rarity_weights"]["1"]
    for seed in range(30):
        for item_id in shop.wandering_stock(1, seed):
            assert items.get_item(item_id)["rarity"] in allowed


def test_the_shop_owner_is_animated_and_still_hops(game, monkeypatch):
    from ui import anim
    merchant = Merchant(3)
    assert len(merchant.frames) > 1                                # the dwarf's idle animation
    clock = {"now": 0.0}
    monkeypatch.setattr(anim, "now", lambda: clock["now"])
    first, _ = merchant.frame()
    clock["now"] = 1 / 6 + 0.01                                    # one picture later
    second, lift = merchant.frame()
    assert first is not second and lift == 0
    merchant.react()
    clock["now"] += 0.17
    assert merchant.frame()[1] > 0


def test_the_shop_has_its_own_music_and_a_welcome_bubble(game):
    music = json.loads((ROOT / "data" / "sounds.json").read_text(encoding="utf-8"))["music"]
    scene = ShopScene(game)
    assert scene.music == "shop" and "shop" in music
    assert (ROOT / "assets" / "sounds" / "music_shop.wav").exists()
    assert scene.bubble.get_width() <= 280 + 4
    scene.draw(game.screen)
