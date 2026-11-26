"""Play the real game many times with pretend players of different skill, and count who wins.

Run:  python tools/simulate_players.py                      (all player types; slow, one run is ~10 s)
      python tools/simulate_players.py --runs 4             (fewer runs per player type: faster, less exact)
      python tools/simulate_players.py --player good --out good.json   (one type, saved to a file)
      python tools/simulate_players.py --summary *.json     (the table, from saved files)

Nothing in the game is changed. It uses the same screens and rules as a real player, with no
window, like tests/test_playthrough.py. A pretend player is described by:

  accuracy  how often they know the answer (0.9 = 9 out of 10 right)
  speed     how many seconds an answer takes: a random number between the two numbers
  potions   whether they drink a healing potion when their HP gets low

They also do what a sensible player does: put on better equipment they find, buy potions in
the shop, and fight every monster before the boss (so they get the experience).
The output is a table: for each kind of player, how many of their runs were won.
"""
import argparse
import json
import os
import random
import sys
from collections import deque
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

PLAYERS = {
    # name: (accuracy, (fastest, slowest seconds), drinks potions)
    "beginner":        (0.50, (6, 14), True),
    "learning":        (0.65, (4, 10), True),
    "average":         (0.75, (3, 8), True),
    "good":            (0.85, (2, 6), True),
    "expert":          (0.95, (1, 3), True),
    "average, no potions": (0.75, (3, 8), False),
}
CLASSES = ["warrior", "mage", "archer"]
HEAL_BELOW = 0.35          # drink a potion when HP is under 35 %
MAX_FRAMES = 40000


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


DIRECTIONS = {(1, 0): pygame.K_RIGHT, (-1, 0): pygame.K_LEFT, (0, 1): pygame.K_DOWN, (0, -1): pygame.K_UP}
NUMBERS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7]


def step(game, *events):
    for event in events:
        game.scenes.current.handle_event(event)
    game.scenes.current.update(1 / 60)        # no draw(): much faster, and nothing is shown anyway


def bfs_step(scene, goal, blocked):
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
            # The goal itself may be a chest or a monster: you walk INTO it to open or fight it.
            if nxt not in came_from and nxt not in blocked and (nxt == goal or scene.floor.is_walkable(*nxt)):
                came_from[nxt] = pos
                todo.append(nxt)
    return None


def next_goal(scene):
    """Chests first, then every normal monster, then the boss, then the stairs."""
    chests = [c["pos"] for c in scene.floor.chests if not c.get("opened")]
    if chests:
        return chests[0]
    normal = [e["pos"] for e in scene.floor.enemies if not e["boss"]]
    if normal:
        return normal[0]
    return scene.floor.enemies[0]["pos"] if scene.floor.enemies else scene.floor.stairs


def wear_upgrades(player, items, inventory):
    """Put on anything in the bag that is better than what is worn."""
    def score(item):
        return player.item_damage_multiplier(item) * 10 + item.get("defense", 0) + item.get("bonus_seconds", 0) * 0.2   # a weapon of another class counts for less
    for item_id in list(player.inventory):
        item = items.get_item(item_id)
        if item["kind"] != "equipment":
            continue
        slot = inventory.slot_for(player, item)
        worn = player.equipped.get(slot)
        if worn is None or score(item) > score(items.get_item(worn)):
            inventory.equip(player, item_id)


def wrong_answer(q):
    if q["type"] == "typed":
        return "xyz"
    if q["type"] == "multi_select":
        return []
    return next(c for c in q["choices"] if c != q["answer"])


def play_one(job):
    name, class_id, seed = job
    accuracy, (fast, slow), potions = PLAYERS[name]
    from combat.combat_scene import CombatScene
    from core import flow
    from core.game import Game
    from dungeon.dungeon_scene import DungeonScene
    from systems import inventory, items, save
    from ui.choice_screen import ChoiceScene
    from ui.screens import EndScene
    from ui.shop_screen import ShopScene
    import tempfile
    save.SAVE_PATH = Path(tempfile.mkdtemp()) / "save.json"     # never touch the real save
    rng = random.Random(f"{name}-{class_id}-{seed}")
    game = Game()
    game.run_state = flow.new_run(class_id, seed=seed)
    flow.enter_floor(game)
    answered = right = crits = potions_drunk = 0
    stuck = 0
    for _ in range(MAX_FRAMES):
        scene = game.scenes.current
        player = game.run_state.player if game.run_state else None
        if isinstance(scene, EndScene):
            return dict(name=name, cls=class_id, won=bool(scene.won), floor=game.run_state.floor_number,
                        level=player.level, answered=answered, right=right, crits=crits, potions=potions_drunk)
        if isinstance(scene, CombatScene):
            if scene.state == "choose":
                heal = [i for i in player.inventory if items.get_item(i)["kind"] == "consumable"
                        and items.get_item(i)["effect"]["type"] == "heal"]
                if potions and heal and player.hp < player.max_hp * HEAL_BELOW:
                    scene.open_items()
                    if scene.state == "items":
                        scene.use_item(scene.item_ids.index(heal[0]))
                        potions_drunk += 1
                        continue
                attacks = [m for m in scene.moves if m["affordable"] and m["questions"] > 0]
                best = max(attacks, key=lambda m: m["damage"] * m["questions"])
                step(game, key(NUMBERS[scene.moves.index(best)]))
            elif scene.state == "question":
                q = scene.battle.question
                seconds = rng.uniform(fast, slow)
                if seconds >= scene.battle.time_limit:
                    scene.elapsed = scene.battle.time_limit       # too slow: the time runs out
                    step(game)
                else:
                    scene.elapsed = seconds
                    knows = rng.random() < accuracy
                    answered += 1
                    right += knows
                    scene.submit(q["answer"] if knows else wrong_answer(q))
                    crits += bool(scene.battle.last_crit)
            else:
                step(game, key(pygame.K_RETURN))
        elif isinstance(scene, ShopScene):
            for _ in range(3):
                step(game, key(pygame.K_RETURN))                  # buy the first thing (a potion) up to 3 times
            wear_upgrades(player, items, inventory)
            step(game, key(pygame.K_ESCAPE) if scene.wandering else key(pygame.K_c))
        elif isinstance(scene, ChoiceScene):
            step(game, key(pygame.K_RETURN))
        elif isinstance(scene, DungeonScene):
            wear_upgrades(player, items, inventory)
            goal = next_goal(scene)
            move = bfs_step(scene, goal, {e["pos"] for e in scene.floor.enemies} - {goal}) or bfs_step(scene, goal, set())
            if move is None:                                       # a chest we cannot reach: forget it
                for c in scene.floor.chests:
                    if c["pos"] == goal:
                        c["opened"] = True
                stuck += 1
                if stuck > 50:
                    break
                continue
            step(game, key(DIRECTIONS[move]))
        else:
            step(game, key(pygame.K_RETURN))
    return dict(name=name, cls=class_id, won=None, floor=None, level=None, answered=answered, right=right,
                crits=crits, potions=potions_drunk)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10, help="runs per player type and class")
    parser.add_argument("--player", choices=list(PLAYERS), help="only this player type")
    parser.add_argument("--out", help="save the results to this JSON file instead of printing the table")
    parser.add_argument("--summary", nargs="+", help="print the table from these saved JSON files")
    args = parser.parse_args()
    if args.summary:
        results = [r for f in args.summary for r in json.loads(Path(f).read_text())]
    else:
        names = [args.player] if args.player else list(PLAYERS)
        results = [play_one((name, cls, seed)) for name in names for cls in CLASSES for seed in range(args.runs)]
        if args.out:
            Path(args.out).write_text(json.dumps(results))
            return
    print_table(results)


def print_table(results):
    print(f"{'player':22} {'won':>9} {'died on floor 1/2/3':>20} {'crit %':>7} {'potions':>8}")
    for name in PLAYERS:
        rows = [r for r in results if r["name"] == name]
        if not rows:
            continue
        done = [r for r in rows if r["won"] is not None]
        won = sum(r["won"] for r in done)
        died = [sum(1 for r in done if not r["won"] and r["floor"] == f) for f in (1, 2, 3)]
        crit = 100 * sum(r["crits"] for r in rows) / max(1, sum(r["answered"] for r in rows))
        drunk = sum(r["potions"] for r in rows) / max(1, len(rows))
        print(f"{name:22} {won:>4}/{len(done):<4} {'/'.join(map(str, died)):>20} {crit:>6.0f}% {drunk:>8.1f}")
        for cls in CLASSES:
            c = [r for r in done if r["cls"] == cls]
            print(f"    {cls:18} {sum(r['won'] for r in c):>4}/{len(c):<4}")
    stuck = len(results) - sum(1 for r in results if r["won"] is not None)
    if stuck:
        print(f"({stuck} runs did not finish and are left out)")


if __name__ == "__main__":
    main()
