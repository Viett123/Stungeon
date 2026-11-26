"""Every weapon belongs to a class; a weapon of another class still works, but weaker."""
import json
from pathlib import Path

import pytest

from systems.player import Player, load_data

ROOT = Path(__file__).resolve().parent.parent
ITEMS = load_data("items.json")
WEAPONS = {item_id: item for item_id, item in ITEMS["items"].items() if item.get("slot") == "weapon"}
CLASSES = ["warrior", "mage", "archer"]
RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]


def test_every_weapon_has_a_class_and_both_pictures():
    for item_id, item in WEAPONS.items():
        assert item["class"] in CLASSES, item_id
        for prefix in ("item_", "weapon_"):
            assert (ROOT / "assets" / "sprites" / f"{prefix}{item_id}.png").exists(), f"{prefix}{item_id}"


@pytest.mark.parametrize("class_id", CLASSES)
def test_every_class_has_a_weapon_of_every_rarity(class_id):
    have = {item["rarity"] for item in WEAPONS.values() if item["class"] == class_id}
    assert have == set(RARITIES)


def test_staffs_are_for_mages_and_bows_for_archers():
    for item_id, item in WEAPONS.items():
        if item.get("attack") == "staff":
            assert item["class"] == "mage", item_id
        if item.get("attack") == "bow":
            assert item["class"] == "archer", item_id


@pytest.mark.parametrize("class_id", CLASSES)
def test_each_class_starts_with_its_own_weapon(class_id):
    start = load_data("classes.json")["classes"][class_id]["start_weapon"]
    assert WEAPONS[start]["class"] == class_id


def test_a_weapon_of_another_class_does_less_damage():
    mage = Player("mage")
    mage.equipped = {"weapon": "mace"}
    assert mage.off_class(WEAPONS["mace"])
    assert mage.damage_multiplier() == pytest.approx(WEAPONS["mace"]["damage_multiplier"] * ITEMS["off_class_damage"])
    mage.equipped = {"weapon": "oak_staff"}
    assert not mage.off_class(WEAPONS["oak_staff"])
    assert mage.damage_multiplier() == pytest.approx(WEAPONS["oak_staff"]["damage_multiplier"])


def test_armour_and_rings_are_never_off_class():
    archer = Player("archer")
    assert not archer.off_class(ITEMS["items"]["gold_ring"])
    assert archer.item_damage_multiplier(ITEMS["items"]["gold_ring"]) == ITEMS["items"]["gold_ring"]["damage_multiplier"]


def test_the_stats_in_each_weapon_text_match_its_numbers():
    for item_id, item in WEAPONS.items():
        assert f"{round((item['damage_multiplier'] - 1) * 100):+d}% damage" in item["text"], item_id
        if item.get("bonus_seconds"):
            assert f"{item['bonus_seconds']:+d}s answer time" in item["text"], item_id


def test_every_new_weapon_can_be_found_or_bought():
    loot = json.dumps(load_data("loot_tables.json")) + json.dumps(load_data("shop.json")["stock"])
    for item_id in ["spiked_club", "hunters_knife", "machete", "double_axe", "frost_staff", "elm_longbow",
                    "moon_blade", "ember_staff", "frost_bow", "starlight_staff", "sunfire_bow"]:
        assert f'"{item_id}"' in loot, item_id


def test_the_details_say_who_a_weapon_is_for_and_warn_in_red():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from core.strings import t
    from ui import item_info, theme
    mage = Player("mage")
    staff = dict(WEAPONS["oak_staff"], id="oak_staff")
    mace = dict(WEAPONS["mace"], id="mace")
    assert item_info.item_lines(staff, mage)[-1] == (t("item_made_for", cls="Mage"), theme.TEXT_DIM)
    text, colour = item_info.item_lines(mace, mage)[-1]
    assert colour == theme.BAD
    assert "Warrior" in text and "-11%" in text and "+19%" in text       # 1.19 x 0.75 = 0.89
    assert len(item_info.item_lines(mace)) == 3                          # no player: as before
