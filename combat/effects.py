"""Status effects: buffs, debuffs and utility moves (owners: B for the rules, D for the content).

PLACEHOLDER. Every function here is a "hook": the battle calls it at a fixed moment
and uses what it returns. Right now each hook does nothing, so there are no effects yet.
To add an effect (for example the Blind debuff), put its rule in the matching hook.
`battle` gives access to battle.player, battle.enemy, battle.engine and battle.rng.

The v1 plan (docs/HANDOFF.md) has 3 buffs and 4 debuffs. Which ones is a design decision.
"""

from combat.damage import round_damage
from systems.player import load_data

def use_utility(move, battle) -> None:
    """Called when the player uses a utility move (War Cry, Reveal, Evasion). No question is asked."""
    # TODO(B/D): start the move's effect, e.g. remember "next attack is stronger" on the battle.


def change_question(question, battle) -> dict:
    """Called for every new question, before it is shown. Return the question to show."""
    # TODO(B): e.g. Blind debuff -> return battle.engine.to_typed(question)
    return question


def change_time_limit(seconds, question, battle) -> int:
    """Called after the default time limit is chosen for a question.

    Equipment can give more time: every worn item's "bonus_seconds" (data/items.json) is added,
    e.g. Worn Boots +2 s. A player without that method (a test's fake player) gets no bonus.
    """
    bonus = getattr(battle.player, "bonus_seconds", lambda: 0)()
    return seconds + bonus


def change_player_damage(damage, battle) -> int:
    """Called after combat/damage.py worked out the player's damage. Return the final number.

    Two rules, both numbers in data/combat.json:
      - a fast answer is a critical hit (the faster, the bigger)
      - a streak of right answers in a row adds damage
    """
    numbers = load_data("combat.json")
    crit = crit_multiplier(battle.time_used, numbers["crit_tiers"])
    streak = streak_multiplier(battle.engine.streak, numbers["streak"])
    battle.last_crit = crit > 1      # so the screen can show "CRIT!"
    return round_damage(damage * crit * streak)


def crit_multiplier(time_used, tiers) -> float:
    """How much a critical hit multiplies the damage, from how fast the answers were.

    time_used: for each answer of the move, the share of its time limit that was used (0.1 = 10 %).
    With several answers (an ultimate has 3), their average decides.
    tiers: from data/combat.json, e.g. [{"within": 0.15, "multiplier": 2.0}, ...].
    """
    if not time_used:
        return 1.0
    average = sum(time_used) / len(time_used)
    for rule in sorted(tiers, key=lambda rule: rule["within"]):
        if average <= rule["within"]:
            return rule["multiplier"]
    return 1.0


def streak_multiplier(streak, rule) -> float:
    """Damage multiplier for a streak of right answers in a row: bonus_per_right each, up to the maximum."""
    return min(rule["max_multiplier"], 1 + rule["bonus_per_right"] * streak)


def item_costs_turn(battle) -> bool:
    """Called after the player used an item in a fight. Return True if that used up the turn.

    Decision: YES. Drinking a potion costs your turn, so the enemy acts next. Why:
      - If a potion were free, the player could heal after every enemy hit and never run low.
        Fights would be too easy, and healing would take away any choice.
      - With the cost, healing is a real choice: heal now and skip your attack, or attack now and risk the hit.
    It is a yes/no design choice, not a balance number, so it stays in code, not in data/.
    """
    return True


def enemy_loses_turn(battle) -> bool:
    """Called before the enemy's turn. Return True to make the enemy skip it.

    After a miss, the enemy skips its turn with a chance (enemy_skip_chance in data/combat.json),
    so one miss is less frustrating. No miss in this round means no skip.
    Uses battle.rng, never the random module, so a fixed seed always gives the same result.
    """
    if not battle.missed:
        return False
    return battle.rng.random() < load_data("combat.json")["enemy_skip_chance"]


def change_enemy_damage(damage, battle) -> int:
    """Called after combat/damage.py worked out the enemy's damage. Return the final number."""
    # TODO(B): e.g. Evasion -> return 0 once.
    return damage


def end_of_round(battle) -> None:
    """Called once after the enemy's turn."""
    # TODO(B): e.g. poison damage, count down how many rounds an effect has left.
