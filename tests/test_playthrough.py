"""A bot plays the real game with no window: title -> class -> 3 floors of fights -> end screen.

It answers every question correctly (it peeks at the answer), so it tests that all
screens, question types and floor changes work together without crashing.
"""
import os
from collections import deque

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat.combat_scene import CombatScene      # noqa: E402
from core.game import Game                        # noqa: E402
from dungeon.dungeon_scene import DungeonScene    # noqa: E402
from ui.screens import EndScene                   # noqa: E402
from ui.shop_screen import ShopScene              # noqa: E402

DIRECTIONS = {(1, 0): pygame.K_RIGHT, (-1, 0): pygame.K_LEFT, (0, 1): pygame.K_DOWN, (0, -1): pygame.K_UP}
NUMBERS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7]


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


def step(game, *events):
    """One frame: hand events to the current scene, then update and draw it."""
    for event in events:
        game.scenes.current.handle_event(event)
    game.scenes.current.update(1 / 60)
    game.scenes.current.draw(game.screen)


def first_step_towards(scene, goal):
    """Walk around other enemies if possible; if one blocks a doorway, walk into it (fight it)."""
    try:
        return _bfs_step(scene, goal, {e["pos"] for e in scene.floor.enemies} - {goal})
    except AssertionError:
        return _bfs_step(scene, goal, set())


def _bfs_step(scene, goal, blocked):
    start = scene.player_pos
    came_from, todo = {start: None}, deque([start])
    while todo:
        pos = todo.popleft()
        if pos == goal:
            while came_from[pos] != start:
                pos = came_from[pos]
            return pos[0] - start[0], pos[1] - start[1]
        for dx, dy in DIRECTIONS:
            nxt = (pos[0] + dx, pos[1] + dy)
            if nxt not in came_from and nxt not in blocked and scene.floor.is_walkable(*nxt):
                came_from[nxt] = pos
                todo.append(nxt)
    raise AssertionError(f"no path to {goal}")


def next_goal(scene):
    """Where the bot walks to: the first normal enemy in the list, then the boss, then the stairs.

    It keeps the same target until that enemy is beaten. (Always walking to the NEAREST
    enemy sounds smarter, but the bot can then bounce forever between two enemies.)
    """
    enemies = scene.floor.enemies
    normal = [e["pos"] for e in enemies if not e["boss"]]
    if normal:
        return normal[0]
    return enemies[0]["pos"] if enemies else scene.floor.stairs


def play_combat_turn(game, scene):
    if scene.state == "choose":
        attacks = [m for m in scene.moves if m["affordable"] and m["questions"] > 0]
        best = max(attacks, key=lambda m: m["damage"] * m["questions"])
        step(game, key(NUMBERS[scene.moves.index(best)]))
    elif scene.state == "question":
        q = scene.battle.question
        if q["type"] == "typed":
            step(game, pygame.event.Event(pygame.TEXTINPUT, text=q["answer"]))
            step(game, key(pygame.K_RETURN))
        elif q["type"] == "multi_select":
            presses = [key(NUMBERS[q["choices"].index(a)]) for a in q["answer"]]
            step(game, *presses, key(pygame.K_RETURN))
        else:
            step(game, key(NUMBERS[q["choices"].index(q["answer"])]))
    else:
        step(game, key(pygame.K_RETURN))


@pytest.mark.parametrize("class_index", [0, 1, 2])
def test_bot_plays_a_whole_run(class_index):
    game = Game()
    step(game, key(pygame.K_RETURN))                      # title -> class select
    step(game, key(NUMBERS[class_index]), key(pygame.K_RETURN))
    answered = 0
    shops = 0

    for _ in range(20000):
        scene = game.scenes.current
        if isinstance(scene, EndScene):
            break
        if isinstance(scene, CombatScene):
            if scene.state == "question":
                answered += 1
            play_combat_turn(game, scene)
        elif isinstance(scene, ShopScene):
            shops += 1
            step(game, key(pygame.K_RETURN))      # try to buy the first item
            step(game, key(pygame.K_c))           # go on to the next floor
        elif isinstance(scene, DungeonScene):
            step(game, key(DIRECTIONS[first_step_towards(scene, next_goal(scene))]))
        else:
            raise AssertionError(f"stuck on {type(scene).__name__}")
    else:
        # The seed makes the failing run repeatable: new_run(class_id, seed=...) gives the same floors.
        raise AssertionError(f"the run never ended (seed {game.run_state.seed})")

    assert isinstance(game.scenes.current, EndScene)
    assert answered > 10
    if game.scenes.current.won:
        assert shops == 2                         # one shop after floor 1 and one after floor 2
    assert game.run_state.engine.stats   # questions were reported
    pygame.quit()
