from systems import save
from systems.enemies import floor_spawns, make_enemy
from systems.player import Player, load_data


def test_level_1_warrior_has_basic_and_skill_moves():
    ids = [m["id"] for m in Player("warrior").unlocked_moves()]
    assert ids == ["slash", "shield_bash"]


def test_level_5_mage_has_all_five_moves():
    assert len(Player("mage", level=5).unlocked_moves()) == 5


def test_moves_carry_their_tier_numbers():
    slash = Player("warrior").unlocked_moves()[0]
    assert slash["difficulty"] == "easy"
    assert {"damage", "cost", "questions"} <= set(slash)


def test_gain_xp_levels_up_and_unlocks_moves():
    # Read the xp needed from the data file, so this test keeps working when D changes the numbers.
    xp_for_level_3 = load_data("progression.json")["xp_for_level"]["3"]
    player = Player("mage")
    hp_before = player.max_hp
    events = player.gain_xp(xp_for_level_3)
    assert events[0] == "level_up:2" and "level_up:3" in events
    assert any(e.startswith("unlocked:") for e in events)
    assert player.level == 3 and player.max_hp > hp_before


def test_hp_never_goes_below_zero_or_above_max():
    player = Player("archer")
    player.take_damage(9999)
    assert player.hp == 0 and not player.alive
    player.heal(9999)
    assert player.hp == player.max_hp


def test_spend_refuses_when_not_enough():
    player = Player("warrior")
    player.resource = 10
    assert not player.spend(15)
    assert player.resource == 10


def test_every_floor_enemy_exists():
    for floor in (1, 2, 3):
        spawns = floor_spawns(floor)
        for enemy_id in spawns["pool"] + [spawns["boss"]]:
            assert make_enemy(enemy_id).hp > 0
        assert make_enemy(spawns["boss"]).boss


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(save, "SAVE_PATH", tmp_path / "save.json")
    assert save.load_game() == {}
    save.save_game({"floor": 2, "player": {"class_id": "archer"}})
    assert save.load_game() == {"floor": 2, "player": {"class_id": "archer"}}
