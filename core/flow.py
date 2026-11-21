"""How the game moves from one screen to the next (owner: lead).

Scenes call these functions instead of creating each other directly, so the order
of the game is written down in one place:

  title menu -> name -> class select -> dungeon -> welcome + level -> floor 1 -> shop -> choice -> floor 2 -> shop -> choice -> floor 3 -> end screen

The game is saved every time a floor starts (never in demo mode).
Scene classes are imported inside the functions, because those files import this one.
"""
from core.run import new_run, run_from_dict, run_to_dict
from core.strings import t
from systems import save, shop
from systems.player import load_data


def start_new_run(game, class_id, name="", subject=None, level=None):
    """name, subject and level were added as keywords with defaults, so start_new_run(game, class_id) still works."""
    game.run_state = new_run(class_id, name=name, subject=subject, level=level)
    enter_floor(game)


# --- the new-game screens ------------------------------------------------------
# What the player picks is collected in game.new_game, one screen at a time.
# Each show_... function opens one screen; Esc on a screen opens the one before it.
def begin_new_game(game):
    game.new_game = {}
    show_name_screen(game)


def show_name_screen(game):
    from ui.new_game import NameScene
    game.scenes.replace(NameScene(game))


def name_chosen(game, name):
    game.new_game["name"] = name
    show_class_select(game)


def show_class_select(game):
    from ui.class_select import ClassSelectScene
    game.scenes.replace(ClassSelectScene(game))


def class_chosen(game, class_id):
    game.new_game["class_id"] = class_id
    show_dungeon_select(game)


def show_dungeon_select(game):
    from ui.new_game import DungeonSelectScene
    game.scenes.replace(DungeonSelectScene(game))


def dungeon_chosen(game, subject):
    from ui.new_game import LevelSelectScene
    game.new_game["subject"] = subject
    game.scenes.replace(LevelSelectScene(game, subject))


def level_chosen(game, level):
    """The last pick: everything is known, so the run starts on floor 1."""
    picks = game.new_game
    start_new_run(game, picks["class_id"], name=picks.get("name", ""),
                  subject=picks["subject"], level=level)


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
        offer_choice(game)


def offer_choice(game):
    """After the shop: the risk-and-reward choice. It then leads to the next floor."""
    from ui.choice_screen import ChoiceScene
    game.scenes.replace(ChoiceScene(game))


def go_to_next_floor(game):
    run = game.run_state
    run.floor_number += 1
    # What the player chose between the floors now becomes this floor's modifiers.
    run.modifiers, run.next_modifiers = run.next_modifiers, {}
    enter_floor(game, [t("new_floor", n=run.floor_number)])


def finish_run(game, won):
    """Show the end screen. A finished run can't be continued; after a defeat the last
    checkpoint stays, so "Continue" starts that floor again (Checkpoint mode)."""
    from ui.screens import EndScene
    if won and not game.run_state.demo:
        save.delete_save()
    game.scenes.replace(EndScene(game, won=won))
