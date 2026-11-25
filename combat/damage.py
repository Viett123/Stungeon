"""The damage formula (owner: B). No pygame here.

PLACEHOLDER. The battle calls these two functions every time damage is dealt.
B decides the real formula; the rest of the game does not need to change.

Ideas the real formula may use (all already available as arguments):
  - move["bonus_damage"]        the ultimate's bonus when all 3 answers are right
  - player.damage_multiplier()  weapons and buffs (owner D)
  - player.level, enemy.boss, how fast the answer was, ...
"""
import math

from systems.player import load_data

# How a number with a decimal point becomes a whole number of damage.
# data/combat.json says which rule to use, by name.
ROUNDING = {
    "round": lambda x: math.floor(x + 0.5),   # half goes up: 12.5 -> 13, 12.4 -> 12
    "floor": math.floor,                      # always down:  12.9 -> 12
    "ceil": math.ceil,                        # always up:    12.1 -> 13
}


def _combat_numbers() -> dict:
    """The numbers in data/combat.json."""
    return load_data("combat.json")


def round_damage(amount) -> int:
    return int(ROUNDING[_combat_numbers()["rounding"]](amount))


def _armour(player) -> int:
    """The player's armour. Until D adds Player.defense(), there is no armour, so 0."""
    if hasattr(player, "defense"):
        return player.defense()
    return 0

def player_damage(move, results, player, enemy) -> int:
    """Damage the player's move deals.

    move    - the move dict (tier numbers merged in, see Player.unlocked_moves)
    results - one True/False per question of this move (an ultimate has 3)
    """
    # TODO(B): the real formula. Placeholder: the tier's damage once per right answer.
    right = sum(results)                   # True counts as 1, False counts as 0
    if right == 0:
        return 0                           # every answer wrong (or none at all): no damage

    hits = move["damage"] * right * player.damage_multiplier()
    # The bonus is added after the multiplier, and only when every answer is right.
    bonus = move.get("bonus_damage", 0) if all(results) else 0
    return round_damage(hits + bonus)



def enemy_damage(enemy, player) -> int:
    """Damage the enemy's attack deals to the player."""
    # TODO(B): the real formula (armour, enemy moves, ...). Placeholder: the enemy's flat number.
    amount = round_damage(enemy.damage - _armour(player))
    return max(amount, _combat_numbers()["min_enemy_damage"])

