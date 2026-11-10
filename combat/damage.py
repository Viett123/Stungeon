"""The damage formula (owner: B). No pygame here.

PLACEHOLDER. The battle calls these two functions every time damage is dealt.
B decides the real formula; the rest of the game does not need to change.

Ideas the real formula may use (all already available as arguments):
  - move["bonus_damage"]        the ultimate's bonus when all 3 answers are right
  - player.damage_multiplier()  weapons and buffs (owner D)
  - player.level, enemy.boss, how fast the answer was, ...
"""


def player_damage(move, results, player, enemy) -> int:
    """Damage the player's move deals.

    move    - the move dict (tier numbers merged in, see Player.unlocked_moves)
    results - one True/False per question of this move (an ultimate has 3)
    """
    # TODO(B): the real formula. Placeholder: the tier's damage once per right answer.
    return move["damage"] * sum(results)


def enemy_damage(enemy, player) -> int:
    """Damage the enemy's attack deals to the player."""
    # TODO(B): the real formula (armour, enemy moves, ...). Placeholder: the enemy's flat number.
    return enemy.damage
