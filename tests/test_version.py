"""The version label in the corner: "v1.0.84 web" (core/version.py)."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from core import version            # noqa: E402
from core.strings import t          # noqa: E402


def test_the_number_has_the_patch_and_a_star_for_uncommitted_changes():
    assert version.number({"patch": 84, "changed": False}) == f"{version.MAJOR_MINOR}.84"
    assert version.number({"patch": 84, "changed": True}) == f"{version.MAJOR_MINOR}.84*"
    assert version.number({}) == version.MAJOR_MINOR          # patch unknown: no number


def test_which_kind_of_build(monkeypatch):
    assert version.kind() == "dev"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert version.kind() == "exe"
    monkeypatch.setattr(sys, "platform", "emscripten")
    assert version.kind() == "web"


def test_a_build_stamp_is_written_and_read_back(tmp_path, monkeypatch):
    monkeypatch.setattr(version, "from_git", lambda: {"patch": 7, "changed": False})
    stamp = tmp_path / "build_stamp.json"
    version.write_stamp(stamp)
    assert version.read_stamp(stamp) == {"patch": 7, "changed": False}
    assert version.read_stamp(tmp_path / "missing.json") == {}


def test_the_stamp_wins_over_git(tmp_path, monkeypatch):
    stamp = tmp_path / "build_stamp.json"
    stamp.write_text('{"patch": 5, "changed": false}', encoding="utf-8")
    monkeypatch.setattr(version, "STAMP_FILE", stamp)
    monkeypatch.setattr(version, "from_git", lambda: {"patch": 99})
    assert version.number() == f"{version.MAJOR_MINOR}.5"


def test_without_git_the_label_still_works(monkeypatch, tmp_path):
    monkeypatch.setattr(version, "STAMP_FILE", tmp_path / "none.json")
    monkeypatch.setattr(version, "_git_once", lambda: {})
    assert version.number() == version.MAJOR_MINOR


def test_every_kind_has_its_text():
    for kind in ("dev", "exe", "web"):
        assert not t(f"version_kind_{kind}").startswith("[")
    assert t("version_label", number="1.0.3", kind="web") == "v1.0.3 web"


def test_the_label_is_drawn_in_the_bottom_right_corner():
    from core import settings
    from core.game import Game
    game = Game()
    game.screen.fill((0, 0, 0))
    game.draw_version()
    w, h = game.version_image.get_size()
    corner = game.screen.subsurface((settings.SCREEN_W - w - 8, settings.SCREEN_H - h - 8, w + 8, h + 8))
    assert any(corner.get_at((x, y))[:3] != (0, 0, 0) for x in range(corner.get_width())
               for y in range(corner.get_height()))


def test_from_git_is_empty_when_git_is_missing(monkeypatch):
    monkeypatch.setattr(version, "_git", lambda *args: None)
    assert version.from_git() == {}
