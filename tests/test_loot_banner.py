"""Rare loot gets a banner and a fanfare; common loot only the usual message."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import flow, sound                 # noqa: E402
from core.game import Game                   # noqa: E402
from systems import items                    # noqa: E402
from systems.player import load_data         # noqa: E402
from ui import loot_banner                   # noqa: E402

ALL = load_data("items.json")["items"]
RARE = next(i for i, item in ALL.items() if item["rarity"] in loot_banner.RARE)
COMMON = next(i for i, item in ALL.items() if item["rarity"] == "common")


@pytest.fixture
def dungeon():
    game = Game()
    flow.start_new_run(game, "warrior")
    return game.scenes.current


def test_only_rare_epic_and_legendary_count_as_rare():
    assert loot_banner.is_rare({"rarity": "legendary"}) and loot_banner.is_rare({"rarity": "rare"})
    assert not loot_banner.is_rare({"rarity": "uncommon"}) and not loot_banner.is_rare({"rarity": "common"})


def test_a_rare_item_gets_a_banner_and_the_fanfare(dungeon, monkeypatch):
    played = []
    monkeypatch.setattr(sound, "play", played.append)
    dungeon.give_items([COMMON])
    assert dungeon.banners == [] and played == []
    dungeon.give_items([RARE])
    assert len(dungeon.banners) == 1 and played == ["rare_loot"]
    assert RARE in dungeon.run.player.inventory


def test_banners_take_turns_and_go_away(dungeon):
    dungeon.give_items([RARE, RARE])
    assert len(dungeon.banners) == 2
    first = dungeon.banners[0]
    dungeon.draw(dungeon.game.screen)
    for _ in range(round(loot_banner.SECONDS * 60) + 2):
        dungeon.update(1 / 60)
    assert first not in dungeon.banners and len(dungeon.banners) == 1


def test_the_banner_fades_in_and_out():
    pygame.init()
    from core.game import load_font
    fonts = {name: load_font(name) for name in ("small", "normal", "big")}
    banner = loot_banner.LootBanner(items.get_item(RARE), fonts)
    assert banner.opacity() == 0
    banner.update(loot_banner.SECONDS / 2)
    assert banner.opacity() == 1
    banner.update(loot_banner.SECONDS / 2 - 0.01)
    assert 0 < banner.opacity() < 0.1


def test_the_fanfare_has_a_recipe_and_a_file():
    from core import settings
    assert "rare_loot" in load_data("sounds.json")["effects"]
    assert (settings.ROOT / "assets" / "sounds" / "rare_loot.wav").exists()
