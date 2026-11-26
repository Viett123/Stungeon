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


def test_spamming_is_counted_across_short_fights():
    """Fights take about 3 answers, so the turns are counted over the floor, not per fight:
    2 Slashes against one enemy and 1 against the next is 3 in a row."""
    habits = HabitTracker()
    first, second = FakeEnemy(), FakeEnemy()
    play_turn(habits, first, "quick")
    play_turn(habits, first, "quick")
    assert play_turn(habits, second, "quick") == "taunt_spam"
    assert first.damage == 10 and second.damage == 12


def test_an_enemy_can_notice_it_when_the_fight_opens():
    """The last blow of a fight has no enemy turn after it; the next enemy still counts it."""
    habits = HabitTracker()
    first, second = FakeEnemy(), FakeEnemy()
    play_turn(habits, first, "quick")
    play_turn(habits, first, "quick")
    habits.record_move("quick", 1, 0.5, True)      # the winning blow: the enemy is dead, no enemy turn
    assert habits.adapt(second) == "taunt_spam"    # the new fight opens (Battle.start)


def test_a_real_fight_opens_with_a_taunt_bubble_after_spamming():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    from combat.combat_scene import CombatScene
    from core import flow
    from core.game import Game
    from systems.enemies import make_enemy
    game = Game()
    game.run_state = flow.new_run("warrior", seed=1)
    flow.enter_floor(game)
    for _ in range(3):
        game.run_state.habits.record_move("slash", "basic", 0.5, True)
        game.run_state.habits.adapt(make_enemy("vocab_slime"))    # three earlier turns, each its own fight
    scene = CombatScene(game, game.run_state.player, make_enemy("article_goblin"), lambda *a: None)
    assert scene.taunt_bubble is not None and scene.taunt_time > 0
    scene.draw(game.screen)


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


# --- weak-spot rule ---------------------------------------------------------------------
class FakeTracker:
    def __init__(self, mastery):
        self.values = mastery

    def mastery(self, topic):
        return self.values.get(topic, 0.5)


class TopicEnemy(FakeEnemy):
    def __init__(self):
        super().__init__()
        self.topics = ["vocabulary"]


def answer(habits, topic, n=1):
    for _ in range(n):
        habits.record_move("slash", 1, 0.5, False, topic=topic)


def test_a_weak_topic_makes_the_enemy_ask_about_it():
    habits = HabitTracker(FakeTracker({"articles": 0.2, "plurals": 0.3}))
    answer(habits, "articles", 3)
    answer(habits, "plurals", 2)                           # 5 answers: enough to judge
    goblin = TopicEnemy()
    assert habits.adapt(goblin) == "taunt_weak_spot"
    assert goblin.topics == ["articles"]                   # the weakest one
    assert habits.taunt_values == {"topic": "articles"}
    assert goblin.damage == 10                             # it does not hit harder


def test_no_weak_spot_before_five_answers_or_without_a_weak_topic():
    habits = HabitTracker(FakeTracker({"articles": 0.2}))
    answer(habits, "articles", 4)
    assert habits.weak_topic() is None                     # too early
    strong = HabitTracker(FakeTracker({"articles": 0.8}))
    answer(strong, "articles", 6)
    assert strong.weak_topic() is None                     # nothing below 0.4


def test_only_topics_that_were_asked_count():
    habits = HabitTracker(FakeTracker({"never_asked": 0.01, "articles": 0.6}))
    answer(habits, "articles", 6)
    assert habits.weak_topic() is None


def test_the_weak_spot_rule_comes_first_and_then_no_other_rule_fires():
    habits = HabitTracker(FakeTracker({"articles": 0.2}))
    answer(habits, "articles", 5)
    goblin = TopicEnemy()
    taunts = [play_turn(habits, goblin, "quick") for _ in range(4)]
    assert taunts == ["taunt_weak_spot", None, None, None]   # one change per enemy: no spam rule now
    assert goblin.damage == 10


def test_an_enemy_already_on_the_weak_topic_is_not_changed_by_it():
    habits = HabitTracker(FakeTracker({"vocabulary": 0.2}))
    answer(habits, "vocabulary", 5)
    assert habits.adapt(TopicEnemy()) is None


def test_a_real_fight_shows_the_weak_spot_taunt_with_the_topic_name():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    from combat.combat_scene import CombatScene
    from core import flow
    from core.game import Game
    from systems.enemies import make_enemy
    game = Game()
    game.run_state = flow.new_run("warrior", seed=1)
    flow.enter_floor(game)
    habits = game.run_state.habits
    habits.tracker = FakeTracker({"plurals": 0.1})
    answer(habits, "plurals", 5)
    shown = []
    from combat import combat_scene
    real_t = combat_scene.t
    combat_scene.t = lambda key, **values: shown.append(real_t(key, **values)) or shown[-1]
    try:
        scene = CombatScene(game, game.run_state.player, make_enemy("article_goblin"), lambda *a: None)
    finally:
        combat_scene.t = real_t
    assert scene.enemy.topics == ["plurals"]                  # changed as soon as the fight opened
    assert scene.taunt_bubble is not None                     # the bubble over the enemy
    assert "I smell your weakness: Plurals!" in shown
    assert any("Article Goblin smells your weakness: Plurals!" in text for text in shown)
