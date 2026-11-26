"""The question screen uses a clear, big font, and every question in every bank still fits."""
import glob
import json
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat import combat_scene                    # noqa: E402
from combat.combat_scene import INSIDE, CombatScene  # noqa: E402
from core import flow, settings                    # noqa: E402
from core.game import Game                         # noqa: E402
from systems.enemies import make_enemy             # noqa: E402

ALL_QUESTIONS = []
for path in glob.glob(str(settings.ROOT / "questions" / "data" / "*.json")):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ALL_QUESTIONS += data["questions"] if isinstance(data, dict) else data


@pytest.fixture(scope="module")
def scene():
    game = Game()
    game.run_state = flow.new_run("warrior", seed=1)
    flow.enter_floor(game)
    return CombatScene(game, game.run_state.player, make_enemy("article_goblin"), lambda *a: None)


def test_every_text_uses_vt323_and_questions_are_bigger_than_normal_text():
    """VT323 is the one font of the game (the chunky Tiny5 was hard to read)."""
    assert {file_name for file_name, _ in settings.FONTS.values()} == {"VT323-Regular.ttf"}
    for name in ("question", "question_small", "answer"):
        assert settings.FONTS[name][1] > settings.FONTS["normal"][1], name


def test_a_short_question_gets_the_big_question_font(scene):
    scene.battle.question = {"question": 'What does "z. B." stand for?', "type": "multiple_choice",
                             "choices": ["zum Beispiel", "zum Bericht"], "answer": "zum Beispiel"}
    scene.layout_question()
    assert scene.question_font is scene.game.fonts["question"]


def test_every_question_in_every_bank_fits_above_the_hint(scene):
    assert len(ALL_QUESTIONS) > 100                    # the banks were really found
    fonts = scene.game.fonts
    hint_top = INSIDE.bottom - fonts["small"].get_height()
    for question in ALL_QUESTIONS:
        scene.battle.question = question
        scene.layout_question()
        text = question["question"][:50]
        assert len(scene.question_lines) <= combat_scene.QUESTION_MAX_LINES + 1, text
        for line in scene.question_lines:
            assert scene.question_font.size(line)[0] <= INSIDE.width, text
        if question["type"] == "typed":
            assert scene.input.rect.bottom <= hint_top, text
            continue
        assert scene.choice_buttons[-1].rect.bottom <= hint_top, text
        for i, choice in enumerate(question["choices"]):
            label = f"{i + 1}. [x] {choice}"               # the longest a label can get (multi_select)
            assert fonts["answer"].size(label)[0] <= INSIDE.width, choice


@pytest.mark.parametrize("kind", ["typed", "multiple_choice", "multi_select"])
def test_the_question_screen_draws(scene, kind):
    scene.state = "choose"
    scene.pick_move(0)                                    # a real move, so the header can be drawn
    scene.battle.question = next(q for q in ALL_QUESTIONS if q["type"] == kind)
    scene.layout_question()
    scene.draw(scene.game.screen)
