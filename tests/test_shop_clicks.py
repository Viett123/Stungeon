"""Clicking rows in the shop (the play-test crash of 26 Nov 2026)."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from core import flow                    # noqa: E402
from core.game import Game               # noqa: E402
from ui.shop_screen import ShopScene     # noqa: E402


def click(scene, row):
    scene.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.rows[row].rect.center))


def test_selling_the_last_row_by_clicking_it_twice_does_not_crash():
    """Click the bottom row to pick it, click again to sell it. It was the only one,
    so the row goes away. The selection must move up, not point past the end."""
    game = Game()
    game.run_state = flow.new_run("warrior", seed=1)
    game.run_state.player.inventory[:] = ["small_potion", "old_sword"]
    shop = ShopScene(game)
    shop.switch_mode()                                    # the Sell tab
    shop.draw(game.screen)
    click(shop, 1)
    assert shop.selected == 1                             # the first click only picks the row
    click(shop, 1)
    assert "old_sword" not in game.run_state.player.inventory
    assert shop.selected == len(shop.entries) - 1 == 0
    shop.draw(game.screen)                                # this line crashed before the fix


def test_clicking_another_row_only_picks_it():
    game = Game()
    game.run_state = flow.new_run("warrior", seed=1)
    game.run_state.player.inventory[:] = ["small_potion", "old_sword"]
    shop = ShopScene(game)
    shop.switch_mode()
    shop.draw(game.screen)
    click(shop, 1)
    assert shop.selected == 1 and game.run_state.player.inventory == ["small_potion", "old_sword"]
