"""The adaptive enemies in ai/habits.py."""
from ai.habits import HabitTracker


class FakeEnemy:
    def __init__(self):
        self.damage = 10
        self.adapted = False


def play_turn(habits, enemy, move, answers=1):
    for _ in range(answers):
        habits.record_move(move, 1, 0.5, True, topic="articles")
    return habits.adapt(enemy)


def test_the_tracker_is_kept():
    assert HabitTracker(tracker="bkt").tracker == "bkt"


def test_the_topic_of_each_answer_is_remembered():
    habits = HabitTracker()
    habits.record_move("quick_strike", 1, 0.5, False, topic="articles")
    assert habits.history[-1]["topic"] == "articles"


def test_three_same_moves_in_a_row_make_the_enemy_stronger():
    habits, goblin = HabitTracker(), FakeEnemy()
    play_turn(habits, goblin, "quick")
    play_turn(habits, goblin, "quick")
    assert play_turn(habits, goblin, "quick") == "taunt_spam"
    assert goblin.damage == 12


def test_mixing_moves_is_not_spamming():
    habits, goblin = HabitTracker(), FakeEnemy()
    for move in ("quick", "heavy", "quick", "heavy"):
        assert play_turn(habits, goblin, move) is None
    assert goblin.damage == 10


def test_one_ultimate_is_not_spamming():
    habits, goblin = HabitTracker(), FakeEnemy()
    assert play_turn(habits, goblin, "ultimate", answers=3) is None
    assert goblin.damage == 10


def test_the_enemy_only_gets_stronger_once():
    habits, goblin = HabitTracker(), FakeEnemy()
    for _ in range(6):
        play_turn(habits, goblin, "quick")
    assert goblin.damage == 12


def test_a_new_enemy_can_adapt_again():
    """Each enemy is thrown away after its fight, like in the game. Python can then give the next
    enemy the same id(), which is why habits.py marks the enemy itself instead of keeping ids."""
    habits = HabitTracker()
    for _ in range(20):
        goblin = FakeEnemy()
        for _ in range(3):
            play_turn(habits, goblin, "quick")
        assert goblin.damage == 12
        del goblin


def test_spamming_in_one_fight_does_not_carry_into_the_next():
    habits = HabitTracker()
    first, second = FakeEnemy(), FakeEnemy()
    for _ in range(3):
        play_turn(habits, first, "quick")
    assert play_turn(habits, second, "quick") is None
    assert second.damage == 10


def test_a_turn_the_enemy_loses_still_counts(monkeypatch):
    """Slash, Slash (the enemy is stunned and loses its turn), Slash: that is 3 turns in a row,
    so the enemy changes on the 3rd turn, not one turn late."""
    import random
    from combat import effects
    from combat.battle import Battle
    from questions.engine import QuestionEngine
    from systems.enemies import make_enemy
    from systems.player import Player
    habits = HabitTracker()
    player = Player("warrior")
    player.hp = player.max_hp = 999
    goblin = make_enemy("article_goblin")
    goblin.hp = goblin.max_hp = 999
    battle = Battle(player, goblin, QuestionEngine(rng=random.Random(1)), floor=1, habits=habits)
    taunts = []
    for turn in range(3):
        monkeypatch.setattr(effects, "enemy_loses_turn", lambda b, stunned=(turn == 1): stunned)
        battle.choose_move("slash")
        battle.answer(battle.question["answer"], 5)
        taunts.append(battle.enemy_turn()["taunt"])
    assert taunts == [None, None, "taunt_spam"]
    assert goblin.adapted
