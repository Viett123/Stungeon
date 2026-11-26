"""Status effects: buffs, debuffs, utility moves, time, crits and streaks (owners: B for the rules, D for the content).

Every function here is a "hook": the battle calls it at a fixed moment and uses what it returns.
`battle` gives access to battle.player, battle.enemy, battle.engine, battle.rng and the
time and answer data of the current move (battle.time_limit, battle.time_used, battle.missed).

Rules that are written: critical hits and streaks (change_player_damage), the three utility
moves (War Cry, Reveal and Evasion, mission 6: use_utility, change_question, change_player_damage
and change_enemy_damage), the enemy skipping its turn after a miss (enemy_loses_turn), and the
item-turn rule (item_costs_turn).
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


def change_time_limit(seconds, question, battle) -> float:
    """Called when a question is shown. `seconds` is the time it gets (by difficulty, plus extra for typed).

    Return the time the question really gets.
    """
    # TODO(B/D): e.g. an armour piece that gives extra seconds -> return seconds + 5
    return seconds


def change_player_damage(damage, battle) -> int:
    """Called after combat/damage.py worked out the player's damage. Return the final number.

    Three multipliers, multiplied together, then rounded once:
      - a fast answer is a critical hit (the faster, the bigger), numbers in data/combat.json
      - a streak of right answers in a row adds damage, numbers in data/combat.json
      - War Cry: the next attack deals more, number in data/combat.json (utility move, mission 6)
    """
    numbers = load_data("combat.json")
    crit = crit_multiplier(battle.time_used, numbers["crit_tiers"])
    streak = streak_multiplier(battle.engine.streak, numbers["streak"])
    war_cry = _use_war_cry(battle, numbers["utility"])
    battle.last_crit = crit > 1      # so the screen can show "CRIT!"
    return round_damage(damage * crit * streak * war_cry)


def _use_war_cry(battle, utility_numbers) -> float:
    """Normally 1.0. After War Cry: the bonus for this attack, and War Cry is used up (hit or miss)."""
    if not battle.war_cry:
        return 1.0
    battle.war_cry = False
    return 1 + utility_numbers["war_cry_bonus"]


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
    """Called once after the enemy's turn."""
    # TODO(B): e.g. poison damage, count down how many rounds an effect has left.
