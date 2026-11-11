"""Animation, chasing monsters and chests."""
import os

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
pygame = pytest.importorskip("pygame")

from combat.combat_scene import CombatScene        # noqa: E402
from core import flow, settings                    # noqa: E402
from core.game import Game                         # noqa: E402
from dungeon import chase                          # noqa: E402
from dungeon.actor import Actor, Animation         # noqa: E402
from dungeon.floor import TREASURE_CHESTS, WALL, generate_floor     # noqa: E402
from systems.enemies import chase_rules, floor_spawns   # noqa: E402

TILE = settings.TILE


# --- animation (plain logic) -------------------------------------------------
def test_animation_shows_each_frame_in_turn_and_loops():
    # Whole seconds, because adding 0.1 six times is not exactly 0.6 on a computer.
    animation = Animation(["a", "b", "c"], seconds_per_frame=1.0)
    seen = []
    for _ in range(7):
        seen.append(animation.image())
        animation.update(1.0)
    assert seen == ["a", "b", "c", "a", "b", "c", "a"]


def make_test_actor():
    frame = pygame.Surface((4, 4))
    return Actor((2, 2), {"idle": [frame], "run": [frame, frame]}, speed=480)


def test_actor_glides_to_the_new_tile_and_stops_exactly_there():
    actor = make_test_actor()
    actor.move_to((3, 2))
    actor.update(0.05)                          # 24 pixels at 480 px/s
    assert actor.moving and actor.x == 2 * TILE + 24
    actor.update(1.0)                           # far longer than needed: must not overshoot
    assert not actor.moving and (actor.x, actor.y) == (3 * TILE, 2 * TILE)


def test_actor_faces_the_way_it_walks():
    actor = make_test_actor()
    actor.move_to((1, 2))
    assert actor.facing_left
    actor.move_to((1, 3))                       # straight down: keeps facing left
    assert actor.facing_left
    actor.move_to((2, 3))
    assert not actor.facing_left


def test_actor_without_hit_frames_uses_idle():
    actor = make_test_actor()
    assert actor.image("hit") is actor.image("idle")


# --- chasing (plain logic) ---------------------------------------------------
class OpenFloor:
    """A floor with no walls except the ones given."""
    grid = []

    def __init__(self, walls=()):
        self.walls = set(walls)

    def is_walkable(self, x, y):
        return (x, y) not in self.walls


def test_distance_counts_diagonals_as_one_step():
    assert chase.distance((0, 0), (2, 2)) == 2
    assert chase.distance((0, 0), (3, 1)) == 3


def test_monster_steps_towards_the_player_and_can_reach_them():
    floor = OpenFloor()
    assert chase.next_step(floor, (5, 5), (8, 5), set()) == (6, 5)
    assert chase.next_step(floor, (5, 5), (5, 3), set()) == (5, 4)
    assert chase.next_step(floor, (5, 5), (6, 5), set()) == (6, 5)       # the player's own tile


def test_monster_goes_around_when_the_straight_step_is_blocked():
    floor = OpenFloor()
    assert chase.next_step(floor, (5, 5), (8, 6), {(6, 5)}) == (5, 6)    # other monster in the way
    assert chase.next_step(OpenFloor(walls={(6, 5), (5, 6)}), (5, 5), (8, 6), set()) is None


def test_a_real_path_from_astar_is_used_when_there_is_one(monkeypatch):
    # Owner C's astar may list the start tile first or not: both work.
    monkeypatch.setattr(chase, "astar", lambda grid, start, goal: [start, (5, 6), (6, 6)])
    assert chase.next_step(OpenFloor(), (5, 5), (8, 5), set()) == (5, 6)
    monkeypatch.setattr(chase, "astar", lambda grid, start, goal: [(4, 5), (4, 6)])
    assert chase.next_step(OpenFloor(), (5, 5), (8, 5), set()) == (4, 5)


# --- chests in the floor -----------------------------------------------------
@pytest.mark.parametrize("number", [1, 2, 3])
def test_chests_are_on_free_floor_cells(number):
    floor = generate_floor(number, seed=11)
    extra = TREASURE_CHESTS if "treasure" in floor.room_kinds else 0     # the treasure room adds its own
    assert len(floor.chests) == floor_spawns(number)["chests"] + extra
    taken = {e["pos"] for e in floor.enemies} | {floor.start, floor.stairs}
    for chest in floor.chests:
        x, y = chest["pos"]
        assert floor.grid[y][x] != WALL and chest["pos"] not in taken and not chest["opened"]
    assert len({c["pos"] for c in floor.chests}) == len(floor.chests)


# --- in the running game -----------------------------------------------------
@pytest.fixture
def dungeon():
    game = Game()
    flow.start_new_run(game, "warrior")
    yield game, game.scenes.current
    pygame.quit()


def frames(game, scene, seconds):
    for _ in range(int(seconds * 60)):
        if game.scenes.current is not scene:
            return
        scene.update(1 / 60)
        scene.draw(game.screen)


def lone_enemy(scene, pos):
    """Keep one normal enemy and put it on pos, so the test controls what happens."""
    enemy = next(e for e in scene.floor.enemies if not e["guard"])     # not a boss or mini-boss: they stand still
    enemy["elite"] = False
    scene.floor.enemies[:] = [enemy]
    enemy["pos"] = pos
    return enemy


def test_a_far_monster_stays_asleep(dungeon):
    game, scene = dungeon
    x, y = scene.player_pos
    enemy = lone_enemy(scene, (x + chase_rules()["wake_radius"] + 1, y))
    frames(game, scene, 2.0)
    assert not enemy["awake"] and enemy["pos"] == (x + chase_rules()["wake_radius"] + 1, y)


def test_a_near_monster_wakes_up_runs_over_and_attacks(dungeon):
    game, scene = dungeon
    x, y = scene.player_pos
    enemy = lone_enemy(scene, (x + 2, y))          # 2 tiles away, in the start room
    frames(game, scene, 3.0)
    assert enemy["awake"]
    assert isinstance(game.scenes.current, CombatScene)   # it reached the player: a fight started


def test_a_monster_rests_after_the_player_runs_away(dungeon):
    game, scene = dungeon
    x, y = scene.player_pos
    enemy = lone_enemy(scene, (x + 1, y))
    scene.start_fight(enemy)
    game.scenes.current.finish(won=False, fled=True)
    assert game.scenes.current is scene and enemy["rest"] > 0
    frames(game, scene, chase_rules()["rest_after_flee"] - 0.5)
    assert game.scenes.current is scene            # still resting: no new fight yet


def test_walking_into_a_chest_opens_it_and_then_you_can_walk_over_it(dungeon):
    game, scene = dungeon
    scene.floor.enemies[:] = []
    x, y = scene.player_pos
    chest = scene.floor.chests[0]
    chest["pos"] = (x + 1, y)
    gold = scene.run.player.gold

    scene.try_move(x + 1, y)
    assert chest["opened"] and scene.player_pos == (x, y)      # the first bump only opens it
    assert scene.run.player.gold > gold
    frames(game, scene, 0.5)                                    # plays the opening animation
    assert scene.chest_image(chest) is scene.chest_frames[-1]
    scene.try_move(x + 1, y)
    assert scene.player_pos == (x + 1, y)


def test_the_player_picture_follows_and_faces_the_move(dungeon):
    game, scene = dungeon
    scene.floor.enemies[:] = []
    scene.floor.chests[:] = []
    x, y = scene.player_pos
    scene.try_move(x - 1, y)
    assert scene.player_actor.facing_left
    frames(game, scene, 0.5)
    assert (scene.player_actor.x, scene.player_actor.y) == ((x - 1) * TILE, y * TILE)
