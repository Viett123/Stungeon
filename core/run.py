"""Everything that belongs to one playthrough, shared by all scenes. No pygame here."""
import random
from dataclasses import dataclass, field

from ai.habits import HabitTracker
from ai.mastery import KnowledgeTracker
from questions.engine import QuestionEngine
from systems.player import Player, load_data

SAVE_VERSION = 3   # raise this when the save format changes, so old saves are ignored


@dataclass
class Run:
    player: Player
    engine: QuestionEngine
    tracker: KnowledgeTracker
    habits: HabitTracker
    seed: int
    floor_number: int = 1
    rng: random.Random = field(default_factory=random.Random)
    demo: bool = False   # exhibit demo: fewer enemies, never saved
    # Changes to a floor chosen between floors (see systems/choices.py), e.g. {"extra_chests": 2}.
    modifiers: dict = field(default_factory=dict)        # for the floor the player is on
    next_modifiers: dict = field(default_factory=dict)   # collected for the next floor


def _make_run(player, seed, tracker, floor_number=1, demo=False) -> Run:
    # The floor number is part of the rng seed, so continuing a save does not replay
    # the exact same questions as the first time on that floor.
    rng = random.Random(f"{seed}-{floor_number}")
    engine = QuestionEngine(rng=rng, tracker=tracker)
    return Run(player=player, engine=engine, tracker=tracker, habits=HabitTracker(),
               seed=seed, floor_number=floor_number, rng=rng, demo=demo)


def new_run(class_id, seed=None, demo=False) -> Run:
    seed = random.randrange(1_000_000) if seed is None else seed
    player = Player(class_id)
    start_weapon = load_data("classes.json")["classes"][class_id].get("start_weapon")
    if start_weapon:
        player.equipped["weapon"] = start_weapon     # a new character holds its class weapon
    return _make_run(player, seed, KnowledgeTracker(), demo=demo)


# --- saving ------------------------------------------------------------------
PLAYER_FIELDS = ["level", "xp", "gold", "hp", "max_hp", "resource", "max_resource", "inventory", "equipped"]


def run_to_dict(run) -> dict:
    """Everything needed to continue this run later, as plain data for systems/save.py."""
    player = {name: getattr(run.player, name) for name in PLAYER_FIELDS}
    player["class_id"] = run.player.class_id
    return {
        "version": SAVE_VERSION,
        "seed": run.seed,
        "floor_number": run.floor_number,
        "player": player,
        "mastery": run.tracker.to_dict(),
        "stats": dict(run.engine.stats),
        "modifiers": dict(run.modifiers),
        # TODO(C): the HabitTracker is not saved yet. Add to_dict/from_dict to it if it should be.
    }


def run_from_dict(data) -> Run:
    """Rebuild a run from run_to_dict's data. Raises ValueError if the data is not usable."""
    if data.get("version") != SAVE_VERSION:
        raise ValueError("save file is from another version")
    saved = data["player"]
    player = Player(saved["class_id"])
    for name in PLAYER_FIELDS:
        # Set the fields after creating the player, so a saved 0 (e.g. no resource left) stays 0.
        setattr(player, name, saved[name])
    run = _make_run(player, data["seed"], KnowledgeTracker.from_dict(data["mastery"]), data["floor_number"])
    run.modifiers = dict(data["modifiers"])
    for topic, counts in data["stats"].items():
        run.engine.stats[topic] = dict(counts)
    return run
