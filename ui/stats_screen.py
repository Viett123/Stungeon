"""The Progress screen: level, XP to the next level, and mastery of every topic (owner: B).

This is the screen that shows the knowledge tracing at the exhibit. The numbers come from
  - ai/mastery.py (owner C): KnowledgeTracker.mastery(topic), a value from 0.0 to 1.0
  - questions/engine.py: how many questions of each topic were asked and answered right
A topic that was never asked shows empty boxes and "not asked yet", so the screen does
not pretend to know something about it.
"""
import pygame

from core.scene import Scene
from core.strings import t
from systems.player import load_data
from ui import theme, topic_names, widgets

PANEL = pygame.Rect(90, 30, 1100, 660)
ROW_HEIGHT = 40
ROWS_PER_COLUMN = 10
PIPS = 10                      # mastery is shown as 10 small boxes; each one stands for 10%
PIP, PIP_GAP = 12, 4
ROW_SHADE = (34, 30, 34)       # every second row is a little lighter, so rows are easy to follow
MASTERY_COLORS = [(0.4, theme.BAD), (0.7, theme.GOLD), (1.01, theme.GOOD)]   # below 40%, below 70%, the rest
CLOSE_KEYS = (pygame.K_ESCAPE, pygame.K_m, pygame.K_RETURN, pygame.K_KP_ENTER)

# Where the parts of a row start, counted from the row's left edge.
NAME_X, PIPS_X, PERCENT_X, COUNTS_X = 10, 262, 430, 478


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


def draw_pips(surface, x, y, mastery, asked):
    """Ten small boxes; as many are filled as the mastery has full tens. None if never asked."""
    filled = round(mastery * PIPS) if asked else 0
    color = mastery_color(mastery)
    for i in range(PIPS):
        box = pygame.Rect(x + i * (PIP + PIP_GAP), y, PIP, PIP)
        pygame.draw.rect(surface, theme.OUTLINE, box.inflate(2, 2))
        pygame.draw.rect(surface, color if i < filled else theme.SLOT_FILL, box)


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
        self.rows = [(topic_names.label(topic), run.tracker.mastery(topic),
                      run.engine.stats.get(topic, {"asked": 0, "correct": 0})) for topic in topics]
        # Asked topics first, weakest of them on top; topics never asked go to the end.
        self.rows.sort(key=lambda row: (row[2]["asked"] == 0, row[1], row[0]))
        self.asked = sum(counts["asked"] for _, _, counts in self.rows)
        self.correct = sum(counts["correct"] for _, _, counts in self.rows)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in CLOSE_KEYS:
            self.game.scenes.pop()

    # --- drawing -------------------------------------------------------------
    def draw(self, surface):
        self.under.draw(surface)
        widgets.dim(surface)
        fonts = self.game.fonts
        inside = theme.draw_frame(surface, PANEL)
        self.draw_header(surface, fonts, inside)
        self.draw_table(surface, fonts, inside)
        widgets.text(surface, fonts["small"], t("stats_hint"), theme.TEXT_DIM, inside.bottomleft, "bottomleft")

    def draw_header(self, surface, fonts, inside):
        """Title, then one line with level, XP bar and how many questions were answered right."""
        small = fonts["small"]
        player = self.player
        widgets.text(surface, fonts["big"], t("stats_title"), theme.GOLD, inside.topleft)
        widgets.text(surface, small, t("stats_streak", n=self.streak), theme.TEXT_DIM, inside.topright, "topright")
        y = inside.y + 56
        widgets.text(surface, fonts["normal"], t("player_label", cls=player.class_name, level=player.level),
                     theme.TEXT, (inside.x, y))
        if self.xp:
            gained, needed = self.xp
            widgets.bar(surface, (inside.x + 220, y + 2, 300, 22), gained, needed, theme.RESOURCE,
                        theme.RESOURCE_BACK, t("stats_xp", xp=gained, needed=needed), small)
        else:
            widgets.text(surface, small, t("stats_max_level"), theme.TEXT_DIM, (inside.x + 220, y + 4))
        percent = round(100 * self.correct / self.asked) if self.asked else 0
        widgets.text(surface, small, t("stats_summary", asked=self.asked, correct=self.correct, percent=percent),
                     theme.TEXT, (inside.right, y + 4), "topright")
        pygame.draw.line(surface, theme.METAL_DARK, (inside.x, y + 40), (inside.right, y + 40), 2)

    def draw_table(self, surface, fonts, inside):
        """Two columns of topic rows under a header line."""
        small = fonts["small"]
        column_width = inside.width // 2
        top = inside.y + 112
        columns = 1 + (len(self.rows) - 1) // ROWS_PER_COLUMN if self.rows else 0
        for column in range(columns):
            x = inside.x + column * column_width
            widgets.text(surface, small, t("stats_header_topic"), theme.GOLD, (x + NAME_X, top))
            widgets.text(surface, small, t("stats_header_mastery"), theme.GOLD, (x + PIPS_X, top))
            widgets.text(surface, small, t("stats_header_answers"), theme.GOLD, (x + COUNTS_X, top))
        for i, (name, mastery, counts) in enumerate(self.rows):
            x = inside.x + (i // ROWS_PER_COLUMN) * column_width
            y = top + 30 + (i % ROWS_PER_COLUMN) * ROW_HEIGHT
            if (i % ROWS_PER_COLUMN) % 2 == 0:
                pygame.draw.rect(surface, ROW_SHADE, (x, y, column_width - 16, ROW_HEIGHT - 4))
            middle = y + (ROW_HEIGHT - 4) // 2
            asked = counts["asked"]
            widgets.text(surface, small, name, theme.TEXT if asked else theme.TEXT_DIM, (x + NAME_X, middle), "midleft")
            draw_pips(surface, x + PIPS_X, middle - PIP // 2, mastery, asked)
            if asked:
                widgets.text(surface, small, t("stats_percent", percent=round(mastery * 100)),
                             mastery_color(mastery), (x + PERCENT_X, middle), "midleft")
                widgets.text(surface, small, t("stats_counts", correct=counts["correct"], asked=asked),
                             theme.TEXT_DIM, (x + COUNTS_X, middle), "midleft")
            else:
                widgets.text(surface, small, t("stats_not_yet"), theme.TEXT_DIM, (x + PERCENT_X, middle), "midleft")
