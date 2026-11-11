"""Title screen. Placeholder until B builds the real menu in ui/."""
import pygame

from core import settings
from core.game import draw_text
from core.scene import Scene
from core.strings import t
from ui import theme


class TitleScene(Scene):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                from ui.class_select import ClassSelectScene
                self.game.message = ""
                self.game.scenes.replace(ClassSelectScene(self.game))
            elif event.key == pygame.K_ESCAPE:
                self.game.quit()

    def draw(self, surface):
        f = self.game.fonts
        cx = settings.SCREEN_W // 2
        theme.draw_frame(surface, (340, 150, 600, 420))
        draw_text(surface, f["title"], t("title"), theme.GOLD, (cx, 260))
        draw_text(surface, f["normal"], t("subtitle"), theme.TEXT_DIM, (cx, 330))
        draw_text(surface, f["big"], t("press_start"), theme.TEXT, (cx, 440))
        draw_text(surface, f["normal"], t("press_quit"), theme.TEXT_DIM, (cx, 490))
        if self.game.message:
            draw_text(surface, f["normal"], self.game.message, theme.BAD, (cx, 640))
