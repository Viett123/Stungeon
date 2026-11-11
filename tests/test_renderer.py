"""Drawing tests, run without a window."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import assets, settings                 # noqa: E402
from dungeon import sprites                       # noqa: E402
from dungeon.camera import Camera                 # noqa: E402
from dungeon.floor import generate_floor          # noqa: E402
from dungeon.renderer import DungeonRenderer      # noqa: E402

TILE = settings.TILE


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.display.set_mode((settings.SCREEN_W, settings.SCREEN_H))
    assets.clear_cache()
    yield surface
    assets.clear_cache()
    pygame.quit()


def test_missing_art_gives_placeholders_of_the_right_size(screen, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)   # an empty folder: no art at all
    for name in ("tile_floor", "tile_wall_front", "tile_stairs", "tile_wall_cap", "tile_wall_side_left",
                 "tile_wall_side_right", "tile_wall_corner_left", "tile_wall_corner_right"):
        assert sprites.tile_sprite(name).get_size() == (TILE, TILE)
    for action in ("idle", "run", "hit"):
        hero = sprites.character_frames("player_warrior", action, (200, 90, 70))
        assert len(hero) == 1                                            # one placeholder picture
        assert hero[0].get_width() == TILE and hero[0].get_height() > TILE   # taller than one tile
    boss = sprites.character_frames("enemy_boss", "idle", (200, 90, 70), big=True)
    assert boss[0].get_width() > TILE
    assert len(sprites.chest_frames()) >= 2


def test_a_real_art_file_is_used_instead_of_the_placeholder(screen, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    art = pygame.Surface((16, 16))
    art.fill((255, 0, 255))
    pygame.image.save(art, str(tmp_path / "tile_floor.png"))
    image = sprites.tile_sprite("tile_floor")
    assert image.get_size() == (TILE, TILE)
    assert image.get_at((10, 10))[:3] == (255, 0, 255)


def test_a_broken_art_file_falls_back_to_the_placeholder(screen, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    (tmp_path / "tile_stairs.png").write_text("this is not a picture")
    assert sprites.tile_sprite("tile_stairs").get_size() == (TILE, TILE)


def test_floor_is_drawn_only_inside_the_view(screen):
    floor = generate_floor(1, seed=4)
    renderer = DungeonRenderer(floor)
    view = pygame.Rect(0, 48, settings.SCREEN_W, settings.SCREEN_H - 48)
    camera = Camera(view.width, view.height, renderer.world_w, renderer.world_h)
    start_x, start_y = floor.start
    camera.snap_to(start_x * TILE + TILE // 2, start_y * TILE + TILE // 2)

    marker = (1, 2, 3)
    screen.fill(marker)
    hero = sprites.character_frames("player_warrior", "idle", (200, 90, 70))[0]
    feet = (start_x * TILE + TILE // 2, (start_y + 1) * TILE)
    renderer.draw(screen, view, camera, [(*feet, hero)])

    assert screen.get_at((5, 5))[:3] == marker                # the status bar area is untouched
    assert screen.get_at((5, 60))[:3] != marker               # the view was drawn
    assert screen.get_clip() == screen.get_rect()             # the clip was reset afterwards
    assert renderer.map_image.get_size() == (floor.width * TILE, floor.height * TILE)
    assert renderer.cap_image.get_size() == renderer.map_image.get_size()


def test_animation_frames_are_found_and_missing_actions_fall_back_to_idle(screen, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    for i in range(3):
        pygame.image.save(pygame.Surface((16, 20)), str(tmp_path / f"enemy_bat_idle_{i}.png"))
    assert len(sprites.character_frames("enemy_bat", "idle", (0, 0, 0))) == 3
    assert len(sprites.character_frames("enemy_bat", "run", (0, 0, 0))) == 3     # no run frames: idle is used


def test_floor_variants_use_their_own_picture_or_the_normal_floor(screen, tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    for name, color in (("tile_floor", (10, 20, 30)), ("tile_floor_3", (200, 100, 50))):
        art = pygame.Surface((16, 16))
        art.fill(color)
        pygame.image.save(art, str(tmp_path / f"{name}.png"))
    assert sprites.tile_sprite("tile_floor", variant=3).get_at((5, 5))[:3] == (200, 100, 50)
    assert sprites.tile_sprite("tile_floor", variant=4).get_at((5, 5))[:3] == (10, 20, 30)


def test_tall_item_art_is_shrunk_to_fit_a_slot(screen, tmp_path, monkeypatch):
    from ui import slots
    monkeypatch.setattr(assets, "SPRITE_DIR", tmp_path)
    monkeypatch.setattr(slots, "_icon_cache", {})
    pygame.image.save(pygame.Surface((10, 21)), str(tmp_path / "item_sword.png"))    # like the pack's swords
    pygame.image.save(pygame.Surface((16, 16)), str(tmp_path / "item_flask.png"))
    font = pygame.font.Font(None, 26)
    assert slots.icon_for("item_sword", (0, 0, 0), "Sw", font).get_size() == (20, 42)   # 2 times, not 3
    assert slots.icon_for("item_flask", (0, 0, 0), "Fl", font).get_size() == (48, 48)


def test_every_art_file_in_the_repo_loads(screen):
    """Catches a broken or misnamed PNG in assets/sprites/ before the exhibit does."""
    for path in sorted(assets.SPRITE_DIR.rglob("*.png")):          # also the theme folders
        name = path.relative_to(assets.SPRITE_DIR).with_suffix("").as_posix()
        assert assets.load_sprite(name) is not None, name
