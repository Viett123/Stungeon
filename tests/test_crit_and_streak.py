"""Tests for critical hits and streaks (mission 4).

A fast answer is a critical hit. Several right answers in a row multiply the damage.
The numbers are in data/combat.json.
"""
from types import SimpleNamespace

import pytest

from combat import effects
from combat.battle import Battle
from systems.enemies import make_enemy
from systems.player import Player, load_data

NUMBERS = load_data("combat.json")
CRIT_TIERS = NUMBERS["crit_tiers"]
STREAK = NUMBERS["streak"]


def fake_battle(time_used, streak=0):
    """A battle with only what the two rules look at."""
    return SimpleNamespace(time_used=time_used, engine=SimpleNamespace(streak=streak), last_crit=False)


@pytest.mark.parametrize("share, expected", [
    (0.05, 2.0),    # fast: inside 8 % of the time
    (0.08, 2.0),    # exactly 8 % still counts
    (0.12, 1.5),    # inside 18 %, but not 8 %
    (0.18, 1.5),    # exactly 18 % still counts
    (0.19, 1.0),    # too slow: no crit
    (0.90, 1.0),
])
def test_crit_multiplier_depends_on_how_fast_the_answer_was(share, expected):
    assert effects.crit_multiplier([share], CRIT_TIERS) == expected


def test_crit_uses_the_average_of_several_answers():
    # (0.04 + 0.2) / 2 = 0.12: inside 18 % but not 8 %, so x1.5
    assert effects.crit_multiplier([0.04, 0.2], CRIT_TIERS) == 1.5


def test_no_answers_means_no_crit():
    assert effects.crit_multiplier([], CRIT_TIERS) == 1.0


# The streak suggestion: +10 % per right answer in a row, up to x1.5.
@pytest.mark.parametrize("streak, expected", [(0, 1.0), (1, 1.1), (2, 1.2), (5, 1.5), (9, 1.5)])
def test_streak_adds_ten_percent_per_right_answer_up_to_one_and_a_half(streak, expected):
    assert effects.streak_multiplier(streak, STREAK) == pytest.approx(expected)


def test_a_fast_answer_doubles_the_damage_and_sets_last_crit():
    battle = fake_battle([0.05])
    assert effects.change_player_damage(10, battle) == 20
    assert battle.last_crit is True


def test_a_slow_answer_is_normal_damage_and_no_crit():
    battle = fake_battle([0.5])
    assert effects.change_player_damage(10, battle) == 10
    assert battle.last_crit is False


def test_last_crit_is_reset_by_the_next_slow_attack():
    battle = fake_battle([0.05])
    effects.change_player_damage(10, battle)
    battle.time_used = [0.9]
    effects.change_player_damage(10, battle)
    assert battle.last_crit is False


def test_streak_alone_adds_damage_without_a_crit():
    battle = fake_battle([0.5], streak=2)      # x1.2, no crit
    assert effects.change_player_damage(10, battle) == 12


def test_streak_and_crit_multiply_together():
    # 10 damage, crit x2, streak of 5 gives x1.5: 10 * 2 * 1.5 = 30
    battle = fake_battle([0.05], streak=5)
    assert effects.change_player_damage(10, battle) == 30


class RightEngine:
    """Asks one question each time. Counts right answers in a row, like the real engine does."""

    def __init__(self):
        self.streak = 0

    def next_question(self, floor, difficulty, topic=None, weakest=False):
        return {"topic": "articles", "type": "multiple_choice", "difficulty": difficulty,
                "question": "___ Bühne", "choices": ["der", "die", "das"], "answer": "die"}

    def check_answer(self, question, given):
        return given == question["answer"]

    def report_answer(self, question, correct, seconds):
        self.streak = self.streak + 1 if correct else 0


def answer_slash(seconds, move_id="shield_bash"):
    """A real warrior fight: one right answer after `seconds` seconds.

    Shield Bash is a skill (medium questions, 20 s), because easy questions can never crit.
    """
    player = Player("warrior")
    player.resource = player.max_resource
    battle = Battle(player, make_enemy("article_goblin"), RightEngine(), floor=1)
    battle.enemy.hp = battle.enemy.max_hp = 1000      # so a big hit is not cut short by the enemy's HP
    slash = next(m for m in battle.moves() if m["id"] == move_id)
    battle.choose_move(slash["id"])
    result = battle.answer("die", seconds)
    return battle, slash, result


def test_a_fast_real_attack_is_a_crit_and_sets_last_crit():
    # Skill questions are medium: 20 s. 0.9 s is 4.5 % of that, so x2.
    # One right answer is a streak of 1, which adds x1.1 on top.
    battle, slash, result = answer_slash(seconds=0.9)
    expected = round(slash["damage"] * 2 * 1.1)
    assert battle.last_crit is True
    assert result["damage"] == expected
    assert battle.enemy.hp == battle.enemy.max_hp - expected


def test_a_slow_real_attack_is_not_a_crit():
    # 10 s is 50 % of 20 s, so no crit. Only the streak of 1 (x1.1) applies.
    battle, slash, result = answer_slash(seconds=10)
    assert battle.last_crit is False
    assert result["damage"] == round(slash["damage"] * 1.1)


def test_extra_seconds_from_items_do_not_make_crits_easier():
    """Worn Boots add time to answer, but the crit is still measured on the normal limit."""
    import random
    from combat.battle import Battle
    from questions.engine import QuestionEngine
    from systems.enemies import make_enemy
    from systems.player import Player
    player = Player("warrior")
    player.bonus_seconds = lambda: 10
    battle = Battle(player, make_enemy("article_goblin"), QuestionEngine(rng=random.Random(5)), floor=1)
    battle.choose_move(battle.moves()[0]["id"])
    assert battle.time_limit == battle.base_time_limit + 10
    seconds = battle.base_time_limit * 0.5
    battle.answer(battle.question["answer"], seconds)
    assert battle.time_used == [0.5]                     # half of the normal limit, not of the longer one


def test_crit_windows_are_tight():
    """After the play-test: a x2 crit needs under 10 % of the time, any crit under 20 %."""
    assert max(rule["within"] for rule in CRIT_TIERS) <= 0.2
    assert min(rule["within"] for rule in CRIT_TIERS) <= 0.1


def test_easy_questions_are_never_a_crit():
    """The basic move asks easy questions: even a very fast right answer is no crit."""
    battle, slash, result = answer_slash(seconds=0.1, move_id="slash")
    assert slash["difficulty"] == "easy"
    assert battle.last_crit is False
    assert result["damage"] == round(slash["damage"] * 1.1)          # only the streak of 1
