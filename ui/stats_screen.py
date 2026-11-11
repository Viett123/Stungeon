"""The Progress screen: level, XP to the next level, and mastery of every topic (owner: B).

This is the screen that shows the knowledge tracing at the exhibit. The numbers come from
  - ai/mastery.py (owner C): KnowledgeTracker.mastery(topic), a value from 0.0 to 1.0
  - questions/engine.py: how many questions of each topic were asked and answered right
While the knowledge tracing is still a placeholder, every topic shows 50%.
"""
import pygame

from core.scene import Scene
from core.strings import t
from systems.player import load_data
from ui import theme, widgets

PANEL = pygame.Rect(110, 40, 1060, 640)
ROW_HEIGHT = 38
ROWS_PER_COLUMN = 10
MASTERY_COLORS = [(0.4, theme.BAD), (0.7, theme.GOLD), (1.01, theme.GOOD)]   # below 40%, below 70%, the rest
CLOSE_KEYS = (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN, pygame.K_KP_ENTER)


def mastery_color(value):
    return next(color for limit, color in MASTERY_COLORS if value < limit)


def xp_progress(player):
    """(xp gained inside this level, xp this level needs), or None at the highest level."""
    table = load_data("progression.json")["xp_for_level"]
    upper = table.get(str(player.level + 1))
    if upper is None:
        return None
    lower = table.get(str(player.level), 0)
    return player.xp - lower, upper - lower


class StatsScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.under = game.scenes.current      # the dungeon, shown darkened behind this screen
        run = game.run_state
        self.player = run.player
        self.streak = run.engine.streak
        self.xp = xp_progress(run.player)
        # Only topics the player can already meet: floor n uses Einheiten 1 to n.
        topics = sorted({q["topic"] for q in run.engine.questions if q["einheit"] <= run.floor_number})
        # Read everything once here; a topic that was never asked has no counts yet.
        self.rows = [(topic, run.tracker.mastery(topic), run.engine.stats.get(topic, {"asked": 0, "correct": 0}))
                     for topic in topics]
        self.rows.sort(key=lambda row: row[1])   # weakest first

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CLOSE_KEYS:
            self.game.scenes.pop()

    def draw(self, surface):
        self.under.draw(surface)
        widgets.dim(surface)
        fonts = self.game.fonts
        small = fonts["small"]
        inside = theme.draw_frame(surface, PANEL)
        player = self.player
        widgets.text(surface, fonts["big"], t("stats_title"), theme.GOLD, inside.topleft)
        widgets.text(surface, fonts["normal"], t("player_label", cls=player.class_name, level=player.level),
                     theme.TEXT, (inside.x, inside.y + 52))
        if self.xp:
            gained, needed = self.xp
            widgets.bar(surface, (inside.x + 230, inside.y + 54, 360, 22), gained, needed, theme.GOLD,
                        theme.SLOT_FILL, t("stats_xp", xp=gained, needed=needed), small)
        else:
            widgets.text(surface, small, t("stats_max_level"), theme.TEXT_DIM, (inside.x + 230, inside.y + 56))
        widgets.text(surface, small, t("stats_streak", n=self.streak), theme.TEXT_DIM, inside.topright, "topright")

        widgets.text(surface, fonts["normal"], t("stats_topics"), theme.GOLD, (inside.x, inside.y + 100))
        column_width = inside.width // 2
        for i, (topic, mastery, counts) in enumerate(self.rows):
            x = inside.x + (i // ROWS_PER_COLUMN) * column_width
            y = inside.y + 140 + (i % ROWS_PER_COLUMN) * ROW_HEIGHT
            widgets.text(surface, small, topic.replace("_", " "), theme.TEXT, (x, y + 2))
            widgets.bar(surface, (x + 250, y, 150, 22), mastery, 1.0, mastery_color(mastery), theme.SLOT_FILL,
                        t("stats_percent", percent=round(mastery * 100)), small)
            widgets.text(surface, small, t("stats_counts", correct=counts["correct"], asked=counts["asked"]),
                         theme.TEXT_DIM, (x + 412, y + 2))
        widgets.text(surface, small, t("stats_hint"), theme.TEXT_DIM, inside.bottomleft, "bottomleft")
