"""The faster drawing for the web version (colorkey instead of see-through pixels) must look
exactly like the old way, and the sound buffer must fit the platform."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import assets, settings, sound          # noqa: E402
from dungeon import sprites, tiles                # noqa: E402
from dungeon.floor import generate_floor          # noqa: E402
from dungeon.renderer import KEY, DungeonRenderer  # noqa: E402
from systems.player import load_data              # noqa: E402
from ui import widgets                            # noqa: E402

TILE = settings.TILE


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.display.set_mode((settings.SCREEN_W, settings.SCREEN_H))
    assets.clear_cache()
    yield surface
    assets.clear_cache()
    pygame.quit()


def old_caps(renderer):
    """The wall tops the old way: a see-through image with per-pixel transparency."""
    image = pygame.Surface((renderer.world_w, renderer.world_h), pygame.SRCALPHA)
    cap = sprites.tile_sprite(tiles.CAP, folder=renderer.folder)
    for y in range(renderer.floor.height):
        for x in range(renderer.floor.width):
            if tiles.has_cap(renderer.floor.grid, x, y):
                image.blit(cap, (x * TILE, y * TILE))
    return image


@pytest.mark.parametrize("theme", ["", "jungle", "desert"])
def test_wall_tops_and_fog_look_exactly_like_before(screen, theme):
    folder = load_data("themes.json")["themes"][theme]["folder"] if theme else ""
    floor = generate_floor(1, seed=4)
    renderer = DungeonRenderer(floor, folder=folder)
    # The same cells lifted from the new fog and from an old-style see-through fog.
    old_fog = pygame.Surface((renderer.world_w, renderer.world_h), pygame.SRCALPHA)
    old_fog.fill(renderer.background)
    cells = [(x, y) for y in range(floor.height) for x in range(floor.width) if (x + y) % 3 == 0]
    renderer.reveal(cells)
    for x, y in cells:
        old_fog.fill((0, 0, 0, 0), (x * TILE, y * TILE, TILE, TILE))

    new = pygame.Surface((renderer.world_w, renderer.world_h))
    old = new.copy()
    for target, caps, fog in ((new, renderer.cap_image, renderer.fog_image), (old, old_caps(renderer), old_fog)):
        target.blit(renderer.map_image, (0, 0))
        target.blit(caps, (0, 0))
        target.blit(fog, (0, 0))
    assert pygame.image.tobytes(new, "RGB") == pygame.image.tobytes(old, "RGB")


def test_no_floor_background_is_the_skip_colour():
    backgrounds = [tuple(theme["background"]) for theme in load_data("themes.json")["themes"].values()]
    assert KEY not in backgrounds + [tuple(sprites.VOID)]


def test_dim_keeps_a_third_of_every_colour(screen):
    surface = pygame.Surface((4, 4))
    surface.fill((255, 150, 30))
    widgets.dim(surface)
    r, g, b = surface.get_at((1, 1))[:3]
    assert abs(r - 85) <= 1 and abs(g - 50) <= 1 and abs(b - 10) <= 1


def test_the_browser_gets_a_bigger_sound_buffer():
    buffers = load_data("sounds.json")["mixer_buffer"]
    assert sound.buffer_size(in_browser=False) == buffers["desktop"]
    assert sound.buffer_size(in_browser=True) == buffers["web"]
    assert buffers["web"] > buffers["desktop"]


def test_the_title_menu_frame_drawn_once_looks_like_drawing_it_every_frame(screen):
    from core import title_scene
    from core.game import Game
    scene = title_scene.TitleScene(Game())
    direct = pygame.Surface((settings.SCREEN_W, settings.SCREEN_H))
    direct.fill((40, 60, 80))
    kept = direct.copy()
    title_scene.draw_mixed_frame(direct, scene.button_frame)
    kept.blit(scene.frame_image, scene.button_frame)
    assert pygame.image.tobytes(direct, "RGB") == pygame.image.tobytes(kept, "RGB")
