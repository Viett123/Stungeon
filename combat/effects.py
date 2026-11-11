"""Status effects: buffs, debuffs and utility moves (owners: B for the rules, D for the content).

PLACEHOLDER. Every function here is a "hook": the battle calls it at a fixed moment
and uses what it returns. Right now each hook does nothing, so there are no effects yet.
To add an effect (for example the Blind debuff), put its rule in the matching hook.
`battle` gives access to battle.player, battle.enemy, battle.engine and battle.rng.

The v1 plan (docs/HANDOFF.md) has 3 buffs and 4 debuffs. Which ones is a design decision.
"""


def use_utility(move, battle) -> None:
    """Called when the player uses a utility move (War Cry, Reveal, Evasion). No question is asked."""
    # TODO(B/D): start the move's effect, e.g. remember "next attack is stronger" on the battle.


def change_question(question, battle) -> dict:
    """Called for every new question, before it is shown. Return the question to show."""
    # TODO(B): e.g. Blind debuff -> return battle.engine.to_typed(question)
    return question


def change_player_damage(damage, battle) -> int:
    """Called after combat/damage.py worked out the player's damage. Return the final number."""
    # TODO(B): e.g. a buff that makes the next attack stronger.
    # TODO(B): two rules from the design doc can go here, the data is ready:
    #   - "the faster you answer, the more critical the attack": battle.seconds is the list of
    #     answer times for this move
    #   - "a streak of correct answers multiplies damage": battle.engine.streak is the number of
    #     right answers in a row (already shown on the fight screen)
    return damage


def item_costs_turn(battle) -> bool:
    """Called after the player used an item in a fight. Return True if that used up the turn."""
    # TODO(B): placeholder rule: using an item costs your turn, so the enemy acts next.
    return True


def enemy_loses_turn(battle) -> bool:
    """Called before the enemy's turn. Return True to make the enemy skip it."""
    # TODO(B): design doc: after a wrong answer there is a chance that the enemy loses its turn too,
    # so a miss is less frustrating. Use battle.rng for the chance and put the number in data/.
    return False


def change_enemy_damage(damage, battle) -> int:
    """Called after combat/damage.py worked out the enemy's damage. Return the final number."""
    # TODO(B): e.g. Evasion -> return 0 once.
    return damage


def end_of_round(battle) -> None:
    """Called once after the enemy's turn."""
    # TODO(B): e.g. poison damage, count down how many rounds an effect has left.
