"""After a fight: what you learned in it, one bar per topic, filling from before to after (owner: B).

The numbers come from the knowledge tracker (ai/mastery.py, owner C): how sure the game is that
you know each topic, from 0 to 1. The fight screen notes the value of each topic just before its
first question (see CombatScene.start_question). At the end of the fight this panel shows
"Articles 34% -> 61%" and a bar that grows from the old value to the new one. A wrong answer can
make a topic go DOWN; that is shown honestly, in red.
"""
import pygame

from core.strings import t
from ui import anim, theme, topic_names, widgets
from ui.stats_screen import mastery_color

MAX_ROWS = 4             # the fight panel has room for this many topics
ROW_HEIGHT = 38
BAR_WIDTH = 300
BAR_HEIGHT = 16
FILL_SECONDS = 1.0       # how long a bar takes to grow from the old value to the new one
NAME_WIDTH = 300         # room for the topic name, left of the bar
BAR_BACK = (40, 36, 42)  # the empty part of a bar (not the red of an HP bar: empty is not "bad")


def learning_rows(before, tracker, max_rows=MAX_ROWS):
    """[(topic, before, after)] for the topics asked in this fight, the biggest change first.

    before: {topic: mastery just before its first question in this fight}."""
    rows = [(topic, value, tracker.mastery(topic)) for topic, value in before.items()]
    rows.sort(key=lambda row: abs(row[2] - row[1]), reverse=True)
    return rows[:max_rows]


def percent(value):
    return round(value * 100)


def draw_learning(surface, fonts, rows, topleft, shown_at):
    """Draw the rows from topleft. shown_at: when the panel appeared (anim.now()), for the filling."""
    if not rows:
        return
    x, y = topleft
    widgets.text(surface, fonts["small"], t("learned_title"), theme.TEXT_DIM, (x, y))
    y += 28
    grow = anim.ease_out(min(1.0, (anim.now() - shown_at) / FILL_SECONDS))
    for topic, before, after in rows:
        widgets.text(surface, fonts["normal"], topic_names.label(topic), theme.TEXT, (x, y))
        bar = pygame.Rect(x + NAME_WIDTH, y + 6, BAR_WIDTH, BAR_HEIGHT)
        pygame.draw.rect(surface, BAR_BACK, bar)
        now = before + (after - before) * grow                     # the bar grows (or shrinks) to the new value
        low, high = min(before, now), max(before, now)
        pygame.draw.rect(surface, theme.TEXT_DIM, (bar.x, bar.y, round(bar.width * low), bar.height))
        change = theme.GOOD if after >= before else theme.BAD
        pygame.draw.rect(surface, change, (bar.x + round(bar.width * low), bar.y,
                                           round(bar.width * (high - low)), bar.height))
        pygame.draw.rect(surface, theme.OUTLINE, bar, 1)
        label = t("learned_change", before=percent(before), after=percent(after))
        widgets.text(surface, fonts["normal"], label, mastery_color(after), (bar.right + 16, y))
        y += ROW_HEIGHT
