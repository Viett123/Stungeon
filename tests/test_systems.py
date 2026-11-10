from systems import save
from systems.player import Player


def test_level_1_warrior_has_basic_and_skill_moves():
    ids = [m["id"] for m in Player("warrior").unlocked_moves()]
    assert ids == ["slash", "shield_bash"]


def test_level_5_mage_has_all_five_moves():
    assert len(Player("mage", level=5).unlocked_moves()) == 5


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(save, "SAVE_PATH", tmp_path / "save.json")
    assert save.load_game() == {}
    save.save_game({"floor": 2, "player": {"class_id": "archer"}})
    assert save.load_game() == {"floor": 2, "player": {"class_id": "archer"}}
