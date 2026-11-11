"""Game over and victory screen with a short learning summary (owner: B)."""
import pygame

from core import settings
from core.scene import Scene
from core.strings import t
from ui import theme, topic_names, widgets


class EndScene(Scene):
    def __init__(self, game, won):
        super().__init__(game)
        self.won = won
        run = game.run_state
        self.player = run.player
        self.floor = run.floor_number
        stats = run.engine.stats
        self.asked = sum(s["asked"] for s in stats.values())
        self.correct = sum(s["correct"] for s in stats.values())
        # Weakest topics first: lowest share of right answers.
        ranked = sorted(stats.items(), key=lambda item: item[1]["correct"] / item[1]["asked"])
        self.weak = [(topic, s) for topic, s in ranked if s["correct"] < s["asked"]][:5]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
            self.game.go_to_title()

    def draw(self, surface):
        f = self.game.fonts
        cx = settings.SCREEN_W // 2
        theme.draw_frame(surface, (240, 50, 800, 620))
        title = t("you_won") if self.won else t("game_over")
        widgets.text(surface, f["title"] if not self.won else f["big"], title,
                     theme.GOOD if self.won else theme.BAD, (cx, 130), "center")
        p = self.player
        widgets.text(surface, f["normal"], t("summary_floor", floor=self.floor, level=p.level, cls=p.class_name),
                     theme.TEXT, (cx, 220), "center")
        percent = round(100 * self.correct / self.asked) if self.asked else 0
        widgets.text(surface, f["normal"], t("summary_answers", correct=self.correct, asked=self.asked, percent=percent),
                     theme.TEXT, (cx, 260), "center")
        if self.weak:
            widgets.text(surface, f["normal"], t("summary_topics"), theme.GOLD, (cx, 330), "center")
            y = 370
            for topic, s in self.weak:
                widgets.text(surface, f["small"], t("summary_topic_line", topic=topic_names.label(topic),
                                                    correct=s["correct"], asked=s["asked"]),
                             theme.TEXT_DIM, (cx, y), "center")
                y += 32
        widgets.text(surface, f["small"], t("back_to_title"), theme.TEXT_DIM, (cx, 630), "center")
