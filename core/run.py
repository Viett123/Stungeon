"""Everything that belongs to one playthrough, shared by all scenes. No pygame here."""
import random
from dataclasses import dataclass, field

from ai.habits import HabitTracker
from ai.mastery import KnowledgeTracker
from questions.engine import QuestionEngine
from systems import dungeons
from systems.player import Player, load_data

SAVE_VERSION = 4   # raise this when the save format changes, so old saves are ignored


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
    # Which dungeon (school subject) and level this run is in, e.g. "german" and "B1".
    subject: str = "german"
    level: str = "B1"


def _make_run(player, seed, tracker, floor_number=1, demo=False, subject=None, level=None) -> Run:
    if subject is None or level is None:
        subject, level = dungeons.default_choice()
    # The floor number is part of the rng seed, so continuing a save does not replay
    # the exact same questions as the first time on that floor.
    rng = random.Random(f"{seed}-{floor_number}")
    # Each level has its own question bank, so the engine loads that level's file.
    engine = QuestionEngine(dungeons.bank_path(subject, level), rng=rng, tracker=tracker)
    return Run(player=player, engine=engine, tracker=tracker, habits=HabitTracker(tracker),
               seed=seed, floor_number=floor_number, rng=rng, demo=demo, subject=subject, level=level)


def new_run(class_id, seed=None, demo=False, name="", subject=None, level=None) -> Run:
    """name, subject and level were added later, as keywords with defaults, so old calls still work."""
    seed = random.randrange(1_000_000) if seed is None else seed
    player = Player(class_id, name=name)
    start_weapon = load_data("classes.json")["classes"][class_id].get("start_weapon")
    if start_weapon:
        player.equipped["weapon"] = start_weapon     # a new character holds its class weapon
    return _make_run(player, seed, KnowledgeTracker(), demo=demo, subject=subject, level=level)


# --- saving ------------------------------------------------------------------
PLAYER_FIELDS = ["name", "level", "xp", "gold", "hp", "max_hp", "resource", "max_resource", "inventory", "equipped"]


def run_to_dict(run) -> dict:
    """Everything needed to continue this run later, as plain data for systems/save.py."""
    player = {name: getattr(run.player, name) for name in PLAYER_FIELDS}
    player["class_id"] = run.player.class_id
    return {
        "version": SAVE_VERSION,
        "seed": run.seed,
        "subject": run.subject,
        "level": run.level,
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
    run = _make_run(player, data["seed"], KnowledgeTracker.from_dict(data["mastery"]), data["floor_number"],
                    subject=data["subject"], level=data["level"])
    run.modifiers = dict(data["modifiers"])
    for topic, counts in data["stats"].items():
        run.engine.stats[topic] = dict(counts)
    return run
