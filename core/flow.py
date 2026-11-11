"""How the game moves from one screen to the next (owner: lead).

Scenes call these functions instead of creating each other directly, so the order
of the game is written down in one place:

  title menu -> class select -> floor 1 -> (shop) -> floor 2 -> (shop) -> floor 3 -> end screen

The game is saved every time a floor starts (never in demo mode).
Scene classes are imported inside the functions, because those files import this one.
"""
from core.run import new_run, run_from_dict, run_to_dict
from core.strings import t
from systems import save, shop
from systems.player import load_data


def start_new_run(game, class_id):
    game.run_state = new_run(class_id)
    enter_floor(game)


def start_demo(game):
    """The exhibit demo: settings come from data/demo.json."""
    demo = load_data("demo.json")
    game.run_state = new_run(demo["class"], seed=demo["seed"], demo=True)
    enter_floor(game)


def continue_run(game) -> bool:
    """Load the saved run and start its floor again. Returns False if there is no usable save."""
    try:
        game.run_state = run_from_dict(save.load_game())
    except (KeyError, TypeError, ValueError):
        return False
    enter_floor(game)
    return True


def can_continue() -> bool:
    """True if there is a saved run that this version of the game can load."""
    try:
        run_from_dict(save.load_game())
    except (KeyError, TypeError, ValueError):
        return False
    return True


def save_checkpoint(game):
    if not game.run_state.demo:
        save.save_game(run_to_dict(game.run_state))


def enter_floor(game, messages=None):
    from dungeon.dungeon_scene import DungeonScene
    save_checkpoint(game)
    game.scenes.replace(DungeonScene(game, messages))


def leave_floor(game):
    """Called when the player steps on the stairs."""
    run = game.run_state
    if run.floor_number >= load_data("progression.json")["last_floor"]:
        finish_run(game, won=True)
    elif shop.stock(run.floor_number):
        from ui.shop_screen import ShopScene
        game.scenes.replace(ShopScene(game))
    else:
        go_to_next_floor(game)


def go_to_next_floor(game):
    run = game.run_state
    run.floor_number += 1
    enter_floor(game, [t("new_floor", n=run.floor_number)])


def finish_run(game, won):
    """Show the end screen. A finished run can't be continued; after a defeat the last
    checkpoint stays, so "Continue" starts that floor again (Checkpoint mode)."""
    from ui.screens import EndScene
    if won and not game.run_state.demo:
        save.delete_save()
    game.scenes.replace(EndScene(game, won=won))
