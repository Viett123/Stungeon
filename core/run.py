"""Everything that belongs to one playthrough, shared by all scenes. No pygame here."""
import random
from dataclasses import dataclass, field

from ai.habits import HabitTracker
from ai.mastery import KnowledgeTracker
from questions.engine import QuestionEngine
from systems.player import Player


@dataclass
class Run:
    player: Player
    engine: QuestionEngine
    tracker: KnowledgeTracker
    habits: HabitTracker
    seed: int
    floor_number: int = 1
    rng: random.Random = field(default_factory=random.Random)


def new_run(class_id, seed=None) -> Run:
    seed = random.randrange(1_000_000) if seed is None else seed
    rng = random.Random(seed)
    tracker = KnowledgeTracker()
    engine = QuestionEngine(rng=rng, tracker=tracker)
    return Run(player=Player(class_id), engine=engine, tracker=tracker,
               habits=HabitTracker(), seed=seed, rng=rng)
