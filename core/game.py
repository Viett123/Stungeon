"""The game loop: read input, update, draw, 60 times a second."""
import logging

import pygame

from core import settings, sound
from core.scene import SceneManager
from core.strings import t

SOUND_NOTICE_SECONDS = 1.5



def load_font(name):
    """One of the fonts in settings.FONTS, e.g. "normal".

    If the font file is missing or broken, pygame's built-in font is used, so the game still runs.
    """
    file_name, size = settings.FONTS[name]
    try:
        return pygame.font.Font(str(settings.FONT_DIR / file_name), size)
    except (OSError, FileNotFoundError):
        logging.error("font %s could not be loaded, using the built-in font", file_name)
        return pygame.font.Font(None, settings.OLD_FONT_SIZES[name])

class Game:
    def __init__(self, fullscreen=False):
        # A small sound buffer (512) makes effects play right when they happen, not a moment later.
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        sound.init()
        self.sound_notice = 0.0   # seconds left to show "Sound on/off" after F2
        flags = pygame.FULLSCREEN | pygame.SCALED if fullscreen else 0
        self.screen = pygame.display.set_mode((settings.SCREEN_W, settings.SCREEN_H), flags)
        pygame.display.set_caption(t("window_title"))
        self.clock = pygame.time.Clock()
        self.running = True
        self.message = ""   # a one-line notice for the title screen (e.g. after an error)

        # Load fonts once here, never inside draw().
        self.fonts = {name: load_font(name) for name in settings.FONTS}
        self.run_state = None   # the current playthrough (core/run.py), set when floor 1 starts
        self.new_game = {}      # name, class, dungeon picked so far on the new-game screens (core/flow.py)

        settings.LOG_DIR.mkdir(exist_ok=True)
        logging.basicConfig(filename=settings.LOG_DIR / "error.log", level=logging.ERROR,
                            format="%(asctime)s %(message)s")

        self.scenes = SceneManager()
        self.go_to_title()

    def go_to_title(self, message=""):
        from core.title_scene import TitleScene   # imported here to avoid a circular import
        self.message = message
        self.scenes.replace(TitleScene(self))

    def draw_sound_notice(self, dt):
        """After F2, show "Sound off (F2)" or "Sound on (F2)" in the bottom left for a moment."""
        if self.sound_notice <= 0:
            return
        self.sound_notice -= dt
        text = t("sound_off") if sound.muted() else t("sound_on")
        image = self.fonts["small"].render(text, True, settings.COLOR_TEXT)
        self.screen.blit(image, (12, settings.SCREEN_H - 30))

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
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                        sound.toggle_mute()   # works on every screen, so it is handled here
                        self.sound_notice = SOUND_NOTICE_SECONDS
                    else:
                        self.scenes.current.handle_event(event)
                self.scenes.current.update(dt)
                sound.follow(self.scenes.current)   # the top screen picks the music
                self.screen.fill(settings.COLOR_BG)
                self.scenes.current.draw(self.screen)
                self.draw_sound_notice(dt)
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
