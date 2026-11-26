"""Status effects: buffs, debuffs, utility moves, time, crits and streaks (owners: B for the rules, D for the content).

Every function here is a "hook": the battle calls it at a fixed moment and uses what it returns.
`battle` gives access to battle.player, battle.enemy, battle.engine, battle.rng and the
time and answer data of the current move (battle.time_limit, battle.time_used, battle.missed).

Rules that are written: critical hits and streaks (change_player_damage), the three utility
moves (War Cry, Reveal and Evasion, mission 6: use_utility, change_question, change_player_damage
and change_enemy_damage), the enemy skipping its turn after a miss (enemy_loses_turn), and the
item-turn rule (item_costs_turn), and the move effects stun (Shield Bash) and poison
(Poison Arrow): after_hit, enemy_loses_turn and poison_tick.
Still placeholders: the other buffs and debuffs. The v1 plan (docs/HANDOFF.md) has
3 buffs and 4 debuffs. Which ones is a design decision.
"""
from combat.damage import round_damage
from systems.player import load_data


def use_utility(move, battle) -> None:
    """Called when the player uses a utility move (War Cry, Reveal, Evasion). No question is asked.

    The move only switches something on, on the battle. The hook that uses it is named below.
    """
    start = UTILITY_EFFECTS.get(move["id"])
    if start is not None:
        start(battle)


def _start_war_cry(battle) -> None:
    # Using War Cry twice before an attack does not stack: it is one flag.
    battle.war_cry = True              # change_player_damage uses it up on the next attack


def _start_reveal(battle) -> None:
    battle.reveal = True               # change_question uses it up on the next multiple-choice question


def _start_evasion(battle) -> None:
    # Using Evasion again starts the count again: the attacks do not add up.
    # change_enemy_damage counts the attacks down.
    battle.evasion_attacks = load_data("combat.json")["utility"]["evasion_attacks"]


# The utility moves, by move id from data/moves.json.
UTILITY_EFFECTS = {"war_cry": _start_war_cry, "reveal": _start_reveal, "evasion": _start_evasion}

# The line shown under a utility move, by move id (keys in core/strings_en.json).
UTILITY_HINTS = {"war_cry": "utility_war_cry", "reveal": "utility_reveal", "evasion": "utility_evasion"}


def change_question(question, battle) -> dict:
    """Called for every new question, before it is shown. Return the question to show.

    Reveal: the next multiple-choice question loses a wrong answer (never the right one).
    Other question types are left alone, and Reveal waits for the next multiple-choice one.
    """
    # TODO(B): e.g. Blind debuff -> return battle.engine.to_typed(question)
    if not battle.reveal or question["type"] != "multiple_choice":
        return question
    battle.reveal = False
    how_many = load_data("combat.json")["utility"]["reveal_wrong_choices_removed"]
    return dict(question, choices=_remove_wrong_choices(question, how_many, battle.rng))


def _remove_wrong_choices(question, how_many, rng) -> list:
    """Copy the choices and take out up to `how_many` wrong ones, picked at random with rng."""
    choices = list(question["choices"])
    for _ in range(how_many):
        wrong = [i for i, choice in enumerate(choices) if choice != question["answer"]]
        if not wrong:
            break                      # no wrong choice is left to take out
        del choices[rng.choice(wrong)]
    return choices


def change_time_limit(seconds, question, battle) -> int:
    """Called after the default time limit is chosen for a question.

    Equipment can give more time: every worn item's "bonus_seconds" (data/items.json) is added,
    e.g. Worn Boots +2 s. A player without that method (a test's fake player) gets no bonus.
    """
    bonus = getattr(battle.player, "bonus_seconds", lambda: 0)()     # heavy weapons give a minus number
    return max(load_data("combat.json")["min_time_limit_seconds"], seconds + bonus)


def change_player_damage(damage, battle) -> int:
    """Called after combat/damage.py worked out the player's damage. Return the final number.

    Three multipliers, multiplied together, then rounded once:
      - a fast answer is a critical hit (the faster, the bigger), but only on the
        difficulties listed in crit_difficulties (now all three, so easy questions can crit too)
      - a streak of right answers in a row adds damage
      - War Cry: the next attack deals more (utility move, mission 6)
    All the numbers are in data/combat.json.
    """
    numbers = load_data("combat.json")
    crit = crit_multiplier(battle.time_used, numbers["crit_tiers"]) if can_crit(battle, numbers) else 1.0
    streak = streak_multiplier(battle.engine.streak, numbers["streak"])
    war_cry = _use_war_cry(battle, numbers["utility"])
    battle.last_crit = crit > 1      # so the screen can show "CRIT!"
    return round_damage(damage * crit * streak * war_cry)


def _use_war_cry(battle, utility_numbers) -> float:
    """Normally 1.0. After War Cry: the bonus for this attack, and War Cry is used up (hit or miss)."""
    if not getattr(battle, "war_cry", False):
        return 1.0
    battle.war_cry = False
    return 1 + utility_numbers["war_cry_bonus"]


def can_crit(battle, numbers) -> bool:
    """Can this move's questions be a crit? Only the difficulties in crit_difficulties can.

    A battle without a move (a test's stand-in) is allowed to crit.
    """
    move = getattr(battle, "move", None)
    if not move:
        return True
    return move.get("difficulty") in numbers.get("crit_difficulties", ["easy", "medium", "hard"])


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
    if getattr(battle, "stunned", False):   # Shield Bash stunned it (after_hit): always skips
        battle.stunned = False
        return True
    if not battle.missed:
        return False
    return battle.rng.random() < load_data("combat.json")["enemy_skip_chance"]


def after_hit(move, damage, battle) -> str | None:
    """Called after a move's last answer. A move with an "effect" in data/moves.json may add it,
    but only when it really hit (damage > 0). Returns "stun", "poison" or None (what happened).

    stun   (Shield Bash): with stun_chance, the enemy loses its next turn.
    poison (Poison Arrow): the enemy loses poison_damage HP at the start of each of its next
           poison_turns turns. Poisoning again starts the count again; it does not add up.
    Numbers: move_effects in data/combat.json.
    """
    effect = move.get("effect")
    if not effect or damage <= 0:
        return None
    numbers = load_data("combat.json")["move_effects"]
    if effect == "stun":
        if battle.rng.random() < numbers["stun_chance"]:
            battle.stunned = True
            return "stun"
        return None
    if effect == "poison":
        battle.poison_turns = numbers["poison_turns"]
        return "poison"
    return None


def poison_tick(battle) -> int:
    """Called at the start of the enemy's turn, also a turn it loses. Returns the HP the
    poison took (0 if it is not poisoned). The enemy can die from it."""
    if getattr(battle, "poison_turns", 0) <= 0:
        return 0
    battle.poison_turns -= 1
    return battle.enemy.take_damage(load_data("combat.json")["move_effects"]["poison_damage"])


def change_enemy_damage(damage, battle) -> int:
    """Called after combat/damage.py worked out the enemy's damage. Return the final number.

    Evasion: while it covers attacks, each enemy attack may miss (0 damage). Every attack that
    is rolled uses up one of its attacks, hit or miss. A skipped enemy turn is not an attack.
    The chance is evasion_miss_chance in data/combat.json, and battle.rng makes the roll.
    """
    if battle.evasion_attacks <= 0:
        return damage
    battle.evasion_attacks -= 1
    if battle.rng.random() < load_data("combat.json")["utility"]["evasion_miss_chance"]:
        return 0
    return damage


def end_of_round(battle) -> None:
    """Called once after the enemy's turn. (Poison is not here: it hurts at the START of the
    enemy's turn, see poison_tick, so it also hurts a stunned enemy and a poisoned enemy that
    dies does not attack first.)"""
