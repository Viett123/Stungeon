"""The game loop: read input, update, draw, 60 times a second."""
import logging

import pygame

from core import settings
from core.scene import SceneManager
from core.strings import t


class Game:
    def __init__(self, fullscreen=False):
        pygame.init()
        flags = pygame.FULLSCREEN | pygame.SCALED if fullscreen else 0
        self.screen = pygame.display.set_mode((settings.SCREEN_W, settings.SCREEN_H), flags)
        pygame.display.set_caption(t("window_title"))
        self.clock = pygame.time.Clock()
        self.running = True
        self.message = ""   # a one-line notice for the title screen (e.g. after an error)

        # Load fonts once here, never inside draw(). Real font files go in assets/fonts later.
        self.fonts = {
            "title": pygame.font.Font(None, 96),
            "big": pygame.font.Font(None, 48),
            "normal": pygame.font.Font(None, 32),
            "small": pygame.font.Font(None, 26),
        }
        self.run_state = None   # the current playthrough (core/run.py), set on the class select screen

        settings.LOG_DIR.mkdir(exist_ok=True)
        logging.basicConfig(filename=settings.LOG_DIR / "error.log", level=logging.ERROR,
                            format="%(asctime)s %(message)s")

        self.scenes = SceneManager()
        self.go_to_title()

    def go_to_title(self, message=""):
        from core.title_scene import TitleScene   # imported here to avoid a circular import
        self.message = message
        self.scenes.replace(TitleScene(self))

    def quit(self):
        self.running = False

    def run(self, max_frames=0):
        frames = 0
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000   # seconds since the last frame
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit()
                    else:
                        self.scenes.current.handle_event(event)
                self.scenes.current.update(dt)
                self.screen.fill(settings.COLOR_BG)
                self.scenes.current.draw(self.screen)
            except Exception:
                # Exhibit rule: never crash. Save the error and go back to the title screen.
                logging.exception("Unhandled error in %s", type(self.scenes.current).__name__)
                self.go_to_title(t("error_returned"))
            pygame.display.flip()

            frames += 1
            if max_frames and frames >= max_frames:
                self.quit()
        pygame.quit()


def draw_text(surface, font, text, color, center):
    """Small helper: draw `text` centred on the point `center`."""
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))
