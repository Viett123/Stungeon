"""After a fight the player sees what they learned: one bar per topic, before -> after."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from ai.mastery import KnowledgeTracker           # noqa: E402
from combat.combat_scene import CombatScene       # noqa: E402
from core import flow                             # noqa: E402
from core.game import Game                        # noqa: E402
from systems.enemies import make_enemy            # noqa: E402
from ui import learning_panel                     # noqa: E402


def test_rows_show_before_and_after_with_the_biggest_change_first():
    tracker = KnowledgeTracker()
    before = {"articles": tracker.mastery("articles"), "plurals": tracker.mastery("plurals")}
    tracker.update("plurals", True)
    tracker.update("plurals", True)
    tracker.update("articles", False)
    rows = learning_panel.learning_rows(before, tracker)
    assert [topic for topic, _, _ in rows] == ["plurals", "articles"]
    plurals, articles = rows
    assert plurals[2] > plurals[1]                     # right answers: up
    assert articles[2] < articles[1]                   # a wrong answer: down, and it is shown


def test_at_most_four_rows_fit():
    tracker = KnowledgeTracker()
    before = {f"topic{i}": 0.3 for i in range(9)}
    assert len(learning_panel.learning_rows(before, tracker)) == learning_panel.MAX_ROWS


@pytest.fixture
def scene():
    game = Game()
    game.run_state = flow.new_run("warrior", seed=1)
    flow.enter_floor(game)
    return CombatScene(game, game.run_state.player, make_enemy("article_goblin"), lambda *a: None)


def test_a_real_fight_notes_the_topic_before_the_answer_and_shows_it_after(scene):
    scene.pick_move(0)                                 # the basic move: one question
    topic = scene.battle.question["topic"]
    before = scene.game.run_state.tracker.mastery(topic)
    assert scene.learned_before == {topic: before}
    scene.submit(scene.battle.question["answer"])      # right answer: mastery goes up
    scene.victory()
    assert scene.learning == [(topic, before, scene.game.run_state.tracker.mastery(topic))]
    assert scene.learning[0][2] > before
    scene.draw(scene.game.screen)                      # the end-of-fight message draws the bars


def test_the_panel_fits_inside_the_fight_panel(scene):
    from combat.combat_scene import INSIDE
    last_row_bottom = INSIDE.y + 6 + 50 + 12 + 28 + learning_panel.MAX_ROWS * learning_panel.ROW_HEIGHT
    assert last_row_bottom < INSIDE.bottom - 24        # above the "press Enter" hint
    width = learning_panel.NAME_WIDTH + learning_panel.BAR_WIDTH + 16 + scene.game.fonts["normal"].size("100% -> 100%")[0]
    assert width <= INSIDE.width
