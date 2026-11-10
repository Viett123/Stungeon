"""Title screen. Placeholder until B builds the real menu in ui/."""
import pygame

from core import settings
from core.game import draw_text
from core.scene import Scene
from core.strings import t


class TitleScene(Scene):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                from dungeon.dungeon_scene import DungeonScene
                self.game.message = ""
                self.game.scenes.replace(DungeonScene(self.game, floor_number=1))
            elif event.key == pygame.K_ESCAPE:
                self.game.quit()

    def draw(self, surface):
        f = self.game.fonts
        cx = settings.SCREEN_W // 2
        draw_text(surface, f["title"], t("title"), settings.COLOR_TEXT, (cx, 250))
        draw_text(surface, f["normal"], t("subtitle"), settings.COLOR_DIM, (cx, 320))
        draw_text(surface, f["big"], t("press_start"), settings.COLOR_TEXT, (cx, 450))
        draw_text(surface, f["normal"], t("press_quit"), settings.COLOR_DIM, (cx, 500))
        if self.game.message:
            draw_text(surface, f["normal"], self.game.message, settings.COLOR_STAIRS, (cx, 640))
