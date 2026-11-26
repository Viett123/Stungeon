from ai.habits import HabitTracker


class FakeEnemy:
    pass


def test_an_enemy_that_already_adapted_is_left_alone():
    habits = HabitTracker()
    goblin = FakeEnemy()
    habits.adapted.add(id(goblin))
    assert habits.adapt(goblin) is None


def test_the_tracker_is_kept():
    habits = HabitTracker(tracker="bkt")
    assert habits.tracker == "bkt"