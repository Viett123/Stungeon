"""Shield Bash can stun, Poison Arrow poisons (combat/effects.py: after_hit, poison_tick)."""
import random

from combat import effects
from combat.battle import Battle
from systems.enemies import make_enemy
from systems.player import Player, load_data

NUMBERS = load_data("combat.json")["move_effects"]


class AlwaysRight:
    """A question engine where every answer is right."""
    streak = 0

    def next_question(self, floor, difficulty, topic=None, weakest=False):
        return {"id": "q", "topic": "articles", "type": "multiple_choice", "choices": ["der", "die"],
                "answer": "der", "difficulty": difficulty}

    def check_answer(self, question, given):
        return given == question["answer"]

    def report_answer(self, question, correct, seconds):
        pass


def fight(class_id, level=5, enemy_hp=999, roll=0.0):
    player = Player(class_id, level=level)
    player.resource = player.max_resource
    player.hp = player.max_hp = 999
    enemy = make_enemy("article_goblin")
    enemy.hp = enemy.max_hp = enemy_hp
    battle = Battle(player, enemy, AlwaysRight(), floor=1, rng=random.Random(0))
    battle.rng.random = lambda: roll          # 0.0: every chance happens, 0.99: none does
    return battle


def use(battle, move_id, right=True):
    battle.choose_move(move_id)
    return battle.answer("der" if right else "die", 10)


def test_the_two_moves_have_their_effect_in_moves_json():
    moves = {m["id"]: m for m in load_data("moves.json")["moves"]}
    assert moves["shield_bash"]["effect"] == "stun"
    assert moves["poison_arrow"]["effect"] == "poison"


def test_shield_bash_can_stun_and_the_enemy_loses_its_next_turn():
    battle = fight("warrior", roll=0.0)
    assert use(battle, "shield_bash")["effect"] == "stun"
    out = battle.enemy_turn()
    assert out["skipped"] and out["damage"] == 0
    battle.rng.random = lambda: 0.99      # no new stun, no skip
    use(battle, "slash")
    assert battle.enemy_turn()["skipped"] is False     # the stun lasted one turn only


def test_shield_bash_does_not_stun_when_the_chance_fails_or_it_misses():
    battle = fight("warrior", roll=NUMBERS["stun_chance"] + 0.01)
    assert use(battle, "shield_bash")["effect"] is None
    missed = fight("warrior", roll=0.0)
    assert use(missed, "shield_bash", right=False)["effect"] is None


def test_poison_hurts_for_its_turns_and_then_stops():
    battle = fight("archer", roll=0.99)
    assert use(battle, "poison_arrow")["effect"] == "poison"
    hp = battle.enemy.hp
    ticks = []
    for _ in range(NUMBERS["poison_turns"] + 1):
        ticks.append(battle.enemy_turn()["poison"])
    assert ticks == [NUMBERS["poison_damage"]] * NUMBERS["poison_turns"] + [0]
    assert battle.enemy.hp == hp - NUMBERS["poison_damage"] * NUMBERS["poison_turns"]


def test_poison_that_kills_ends_the_fight_without_an_enemy_attack():
    battle = fight("archer", roll=0.99)
    use(battle, "poison_arrow")
    battle.enemy.hp = 3
    hp = battle.player.hp
    out = battle.enemy_turn()
    assert battle.won and out["damage"] == 0 and battle.player.hp == hp


def test_poison_also_hurts_a_stunned_enemy():
    battle = fight("archer", roll=0.99)
    use(battle, "poison_arrow")
    battle.stunned = True
    out = battle.enemy_turn()
    assert out["skipped"] and out["poison"] == NUMBERS["poison_damage"]


def test_poisoning_again_starts_the_count_again():
    battle = fight("archer", roll=0.99)
    use(battle, "poison_arrow")
    battle.enemy_turn()
    use(battle, "poison_arrow")
    assert battle.poison_turns == NUMBERS["poison_turns"]


def test_a_killing_blow_has_no_effect():
    battle = fight("archer", enemy_hp=5, roll=0.99)
    assert use(battle, "poison_arrow")["effect"] is None


def _scene(class_id):
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    from combat.combat_scene import CombatScene
    from core import flow
    from core.game import Game
    game = Game()
    game.run_state = flow.new_run(class_id, seed=1)
    flow.enter_floor(game)
    return CombatScene(game, game.run_state.player, make_enemy("article_goblin"), lambda *a: None)


def test_the_fight_screen_says_the_enemy_is_stunned():
    from core.strings import t
    scene = _scene("warrior")
    scene.battle.stunned = True
    scene.enemy_turn()
    assert scene.lines[0][0] == t("enemy_stunned_turn", enemy=scene.enemy_name)


def test_the_fight_screen_wins_when_the_poison_finishes_the_enemy():
    from core.strings import t
    scene = _scene("archer")
    scene.battle.poison_turns = 1
    scene.battle.enemy.hp = 2
    won = []
    scene.victory = lambda: won.append(True)
    scene.enemy_turn()
    assert scene.lines[0][0] == t("effect_poison_tick", enemy=scene.enemy_name, damage=2)
    scene.next_step()
    assert won == [True]
