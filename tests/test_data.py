"""The data files must load and fit together, whatever numbers the owners choose."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def test_every_data_file_is_valid_json():
    for path in DATA.glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_every_move_has_a_known_class_and_tier():
    moves, classes = load("moves.json"), load("classes.json")["classes"]
    for move in moves["moves"]:
        assert move["class"] in classes, move["id"]
        assert move["tier"] in moves["tiers"], move["id"]


def test_every_class_has_a_free_question_move_at_level_1():
    # Without one, a player with no resource left could not do anything in a fight.
    moves = load("moves.json")
    for class_id in load("classes.json")["classes"]:
        tiers = [moves["tiers"][m["tier"]] for m in moves["moves"] if m["class"] == class_id]
        assert any(t["cost"] == 0 and t["questions"] > 0 and t["unlock_level"] == 1 for t in tiers), class_id


def test_question_tiers_use_difficulties_from_the_bank():
    for name, tier in load("moves.json")["tiers"].items():
        if tier["questions"] > 0:
            assert tier["difficulty"] in ("easy", "medium", "hard"), name


def test_enemy_topics_exist_in_the_question_bank():
    bank = json.loads((DATA.parent / "questions" / "data" / "questions_german_b1.json").read_text(encoding="utf-8"))
    topics = {q["topic"] for q in bank["questions"]}
    for enemy_id, enemy in load("enemies.json")["enemies"].items():
        assert set(enemy.get("topics", [])) <= topics, enemy_id


def test_every_floor_up_to_the_last_has_spawns():
    floors = load("enemies.json")["floors"]
    for number in range(1, load("progression.json")["last_floor"] + 1):
        assert str(number) in floors
