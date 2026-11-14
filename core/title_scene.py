"""The title menu: New game, Continue, Demo, Quit (owner: lead)."""
import pygame

from core import flow, settings
from core.strings import t
from ui import theme, widgets
from ui.menu import MenuScene


class TitleScene(MenuScene):
    def __init__(self, game):
        options = [
            (t("menu_new_game"), self.new_game, True),
            (t("menu_continue"), self.continue_game, flow.can_continue()),   # greyed out without a save
            (t("menu_demo"), lambda: flow.start_demo(game), True),
            (t("menu_credits"), self.show_credits, True),
            (t("menu_quit"), game.quit, True),
        ]
        super().__init__(game, t("title"), options, top=270)

    def new_game(self):
        from ui.class_select import ClassSelectScene
        self.game.message = ""
        self.game.scenes.replace(ClassSelectScene(self.game))

    def show_credits(self):
        from ui.credits_screen import CreditsScene
        self.game.scenes.replace(CreditsScene(self.game))

    def continue_game(self):
        if not flow.continue_run(self.game):
            self.game.message = t("save_unusable")

    def handle_event(self, event):
        # One key starts the exhibit demo straight from the title screen.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            flow.start_demo(self.game)
        else:
            super().handle_event(event)

    def on_escape(self):
        self.game.quit()

    def draw(self, surface):
        super().draw(surface)
        fonts = self.game.fonts
        cx = settings.SCREEN_W // 2
        widgets.text(surface, fonts["small"], t("subtitle"), theme.TEXT_DIM, (cx, self.frame.y + 92), "center")
        widgets.text(surface, fonts["small"], t("menu_hint"), theme.TEXT_DIM, (cx, 690), "center")
        if self.game.message:
            widgets.text(surface, fonts["normal"], self.game.message, theme.BAD, (cx, 100), "center")
