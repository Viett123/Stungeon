"""Tests for the made-in-code sounds (tools/make_sounds.py) and the sound player (core/sound.py)."""
import json
import os
import random
import re
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import sound  # noqa: E402
from tools import make_sounds  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RECIPES = json.loads((ROOT / "data" / "sounds.json").read_text(encoding="utf-8"))
RATE = RECIPES["sample_rate"]


# --- making the sounds ------------------------------------------------------
def test_note_names_give_the_right_pitch():
    assert make_sounds.note_hz("A4") == pytest.approx(440)
    assert make_sounds.note_hz("A5") == pytest.approx(880)      # one octave up = twice as high
    assert make_sounds.note_hz("C4") == pytest.approx(261.63, abs=0.01)
    assert make_sounds.note_hz("Bb3") == pytest.approx(make_sounds.note_hz("A#3"))


def test_every_effect_is_made_at_its_planned_loudness():
    for name, recipe in RECIPES["effects"].items():
        samples = make_sounds.make_effect(recipe, RATE, random.Random(name))
        assert samples, name
        assert all(-1.0 <= v <= 1.0 for v in samples), name
        assert max(abs(v) for v in samples) == pytest.approx(recipe.get("volume", 1.0)), name
        assert len(samples) / RATE < 2.0, f"{name} is too long for an effect"


def test_the_same_recipe_always_gives_the_same_sound():
    recipe = RECIPES["effects"]["hit"]       # has noise in it, which uses random numbers
    first = make_sounds.make_effect(recipe, RATE, random.Random("hit"))
    again = make_sounds.make_effect(recipe, RATE, random.Random("hit"))
    assert first == again


def test_music_tracks_are_whole_bars_and_use_known_notes():
    for name, song in RECIPES["music"].items():
        lengths = set()
        for track in song["tracks"]:
            steps = make_sounds.steps_of(track)
            lengths.add(len(steps))
            for token in steps:
                if token in ("-", "."):
                    continue
                if track["wave"] == "drums":
                    assert set(token) <= set(make_sounds.DRUMS), (name, token)
                else:
                    make_sounds.note_hz(token)     # raises if the note name is wrong
        # All tracks of a song must be the same length, in whole bars of 8, or the loop drifts.
        assert len(lengths) == 1, f"{name}: tracks have different lengths {lengths}"
        assert lengths.pop() % 8 == 0, name


def test_a_music_loop_lasts_exactly_its_steps():
    song = {"bpm": 120, "tracks": [{"wave": "square", "steps": "A4 - . . | C5 - - -"},
                                   {"wave": "drums", "steps": "k . s . | k . s ."}]}
    samples = make_sounds.make_music(song, RATE, random.Random(1))
    # 8 steps of an eighth note at 120 beats a minute = 8 * 0.25 s = 2 seconds.
    assert len(samples) == int(8 * 0.25 * RATE)
    assert all(-1.0 <= v <= 1.0 for v in samples)


def test_build_writes_wav_files(tmp_path):
    recipes = dict(RECIPES, effects={"hit": RECIPES["effects"]["hit"]},
                   music={"tiny": {"bpm": 120, "tracks": [{"wave": "triangle", "steps": "A3 - - - C4 - E4 -"}]}})
    assert make_sounds.build(recipes, tmp_path) == ["hit", "music_tiny"]
    assert (tmp_path / "hit.wav").stat().st_size > 1000
    assert (tmp_path / "music_tiny.wav").exists()


# --- the game uses only sounds that exist -------------------------------------
def code_files():
    for folder in ("combat", "core", "dungeon", "ui", "systems"):
        yield from (ROOT / folder).glob("*.py")


def test_every_sound_the_code_plays_has_a_recipe_and_a_file():
    played = set()
    for path in code_files():
        played |= set(re.findall(r'sound\.play\("(\w+)"', path.read_text(encoding="utf-8")))
        for a, b in re.findall(r'sound\.play\("(\w+)" if .+? else "(\w+)"\)', path.read_text(encoding="utf-8")):
            played |= {a, b}
    played |= set(RECIPES["skill_kinds"].values())
    assert len(played) > 10
    for name in played:
        assert name in RECIPES["effects"], f"no recipe for the sound {name!r}"
        assert (sound.SOUND_DIR / f"{name}.wav").exists(), f"run python tools/make_sounds.py ({name})"


def test_every_music_the_screens_ask_for_has_a_file():
    asked = {"fight", "boss"}                # chosen in combat_scene.py
    for path in code_files():
        asked |= set(re.findall(r'^\s+music = "(\w+)"', path.read_text(encoding="utf-8"), re.M))
    asked.discard("off")
    assert {"title", "dungeon"} <= asked
    for name in asked:
        assert name in RECIPES["music"], name
        assert (sound.SOUND_DIR / f"music_{name}.wav").exists(), name


def test_every_move_kind_has_a_sound():
    looks = json.loads((ROOT / "data" / "skill_looks.json").read_text(encoding="utf-8"))
    kinds = {look["kind"] for look in looks["looks"].values()} | {looks["default"]["kind"]}
    assert kinds <= set(RECIPES["skill_kinds"])


# --- playing them -------------------------------------------------------------
@pytest.fixture
def mixer():
    pygame.init()
    sound.reset()
    yield sound.init()
    sound.reset()


def test_playing_never_crashes(mixer):
    sound.play("hit")
    sound.play("no_such_sound")            # a missing file is just silence
    sound.play_music("no_such_track")


def test_without_a_sound_card_nothing_happens(monkeypatch):
    sound.reset()
    monkeypatch.setitem(sound._state, "ready", False)
    sound.play("hit")
    sound.play_music("dungeon")
    assert sound.current_music() == "dungeon"   # remembered, so nothing restarts later


def test_screens_choose_the_music(mixer):
    class Screen:
        music = None
    dungeon, menu = Screen(), Screen()
    dungeon.music = "dungeon"
    sound.follow(dungeon)
    assert sound.current_music() == "dungeon"
    sound.follow(menu)                       # music = None: keep playing what is on
    assert sound.current_music() == "dungeon"


def test_f2_turns_sound_off_and_on(mixer):
    assert sound.toggle_mute() is True
    assert sound.muted()
    sound.play("hit")                        # quiet, and no crash
    assert sound.toggle_mute() is False


def test_f2_works_in_the_running_game(mixer):
    from core.game import Game
    game = Game()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F2, mod=0, unicode=""))
    game.run(max_frames=2)
    assert sound.muted()
    assert sound.current_music() == "title"
