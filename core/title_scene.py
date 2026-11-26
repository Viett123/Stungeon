"""The title menu: New game, Continue, Demo, Credits, Quit (owner: lead).

It looks like a torch-lit dungeon room cut into the three floor looks, jungle | stone | desert
(ui/backdrop.py), with the game's name at the top and the three heroes standing guard beside
the menu. The menu's frame is made of all three biome frames, one third each.
"""
import pygame

from core import assets, flow, settings
from core.strings import t
from dungeon.actor import make_actor
from systems.player import load_data
from ui import anim, theme, widgets
from ui.backdrop import Backdrop, biome_columns
from ui.menu import BUTTON_H, BUTTON_W, GAP, MenuScene

MENU_TOP = 370            # y of the first button
LOGO_TOP = 12             # y of the top of the logo
SUBTITLE_GAP = 22         # pixels between the bottom of the logo and the middle of the subtitle
LOGO_SCALE = 1.6          # the name is drawn this much bigger than the title font
LOGO_MAX = (1100, 280)    # the biggest a drawn logo may be on screen (width, height): it must end above the subtitle
LOGO_FILE = "logo"        # assets/sprites/logo.png: if it exists, it is used instead of the logo made in code
HERO_FEET_Y = 600         # where the heroes beside the menu stand
HERO_SPOTS = [("warrior", 250, False), ("mage", 1030, True), ("archer", 1130, True)]   # (class, x, facing left)


def _logo(font, string):
    """The game's name in gold with a dark outline, made once.

    The outline is the same text in a dark colour, drawn one pixel away in every
    direction under the gold text. Scaling up afterwards keeps the chunky pixel look.
    """
    gold = font.render(string, True, theme.GOLD)
    dark = font.render(string, True, theme.OUTLINE)
    width, height = gold.get_size()
    logo = pygame.Surface((width + 6, height + 8), pygame.SRCALPHA)
    for dx in (-1, 0, 1, 2, 3):
        for dy in (-1, 0, 1, 2, 3, 4):
            logo.blit(dark, (dx + 2, dy + 2))      # a thick outline that is deeper at the bottom right
    logo.blit(gold, (2, 2))
    bright = font.render(string, True, theme.GOLD_BRIGHT)
    top_half = bright.subsurface((0, 0, width, height // 2 - 4))
    logo.blit(top_half, (2, 2))                    # a lighter top half, like light from above
    size = (round(logo.get_width() * LOGO_SCALE), round(logo.get_height() * LOGO_SCALE))
    return pygame.transform.scale(logo, size)


def _drawn_logo():
    """The logo someone drew: assets/sprites/logo.png, or None if there is no such file.

    Pixel art is resized by a whole number, so every pixel stays a sharp square:
      - a small picture is made 2, 3, 4... times BIGGER, as big as fits inside LOGO_MAX
      - a big picture is made 2, 3, 4... times SMALLER, until it fits. A logo drawn with
        8-screen-pixel squares then becomes clean 4-pixel squares at half size, not a blur.
    """
    image = assets.load_sprite(LOGO_FILE, factor=1)
    if image is None:
        return None
    width, height = image.get_size()
    factor = min(LOGO_MAX[0] // width, LOGO_MAX[1] // height)
    if factor >= 1:
        return assets.scale_up(image, factor)
    divide = 2
    while width / divide > LOGO_MAX[0] or height / divide > LOGO_MAX[1]:
        divide += 1
    # transform.scale (not smoothscale) keeps the hard pixel edges.
    return pygame.transform.scale(image, (width // divide, height // divide))


def _glow(size):
    """A soft orange light for behind the logo, as if a torch lit it from below."""
    small = pygame.Surface((32, 12), pygame.SRCALPHA)
    for step in range(6, 0, -1):
        rect = pygame.Rect(0, 0, 32 * step / 6, 12 * step / 6)
        rect.center = (16, 6)
        pygame.draw.ellipse(small, (255, 150, 60, 14 * (7 - step)), rect)
    return pygame.transform.smoothscale(small, size)


def draw_mixed_frame(surface, rect):
    """The menu frame in three slices: the left third uses the jungle frame, the middle the stone
    one, the right the desert one, in the same order as the biomes behind it.

    Each frame is drawn whole, but a clip rectangle lets only its own slice reach the screen.
    """
    rect = pygame.Rect(rect)
    folders = [folder for _, folder, _ in biome_columns()]
    third = rect.width // len(folders)
    old_clip = surface.get_clip()
    for i, folder in enumerate(folders):
        right = rect.right if i == len(folders) - 1 else rect.x + (i + 1) * third
        surface.set_clip(pygame.Rect(rect.x + i * third, rect.y, right - rect.x - i * third, rect.height))
        theme.draw_frame(surface, rect, style=folder)
    surface.set_clip(old_clip)


class TitleScene(MenuScene):
    music = "title"   # core/sound.py: the title tune keeps playing through the new-game screens

    def __init__(self, game):
        options = [
            (t("menu_new_game"), self.new_game, True),
            (t("menu_continue"), self.continue_game, flow.can_continue()),   # greyed out without a save
            (t("menu_demo"), lambda: flow.start_demo(game), True),
            (t("menu_credits"), self.show_credits, True),
            (t("menu_quit"), game.quit, True),
        ]
        super().__init__(game, t("title"), options, top=MENU_TOP)
        # Everything below is made once here, never inside draw().
        self.backdrop = Backdrop(biomes=True)
        theme.set_frame_style("")     # back at the title: other menus use the stone frame until a floor starts
        # A drawn logo (assets/sprites/logo.png) wins; without one, the logo is made from the font.
        self.logo = _drawn_logo() or _logo(game.fonts["title"], t("title").upper())
        self.logo_rect = self.logo.get_rect(midtop=(settings.SCREEN_W // 2, LOGO_TOP))
        self.subtitle_y = self.logo_rect.bottom + SUBTITLE_GAP
        self.glow = _glow((self.logo.get_width() + 200, self.logo.get_height() + 60))
        self.button_frame = pygame.Rect(0, 0, BUTTON_W + 60, len(options) * (BUTTON_H + GAP) + 40)
        self.button_frame.midtop = (settings.SCREEN_W // 2, MENU_TOP - 25)
        # The three-part frame is drawn once into its own picture, not three times every frame.
        self.frame_image = pygame.Surface(self.button_frame.size, pygame.SRCALPHA)
        draw_mixed_frame(self.frame_image, self.frame_image.get_rect())
        # Speed (it matters in the web version): RLEACCEL lets pygame jump over the see-through
        # parts of a picture instead of blending every pixel. These three never change.
        for image in (self.logo, self.glow, self.frame_image):
            image.set_alpha(255, pygame.RLEACCEL)
        classes = load_data("classes.json")["classes"]
        self.heroes = []
        for class_id, x, facing_left in HERO_SPOTS:
            actor = make_actor(f"player_{class_id}", (0, 0), tuple(classes[class_id].get("color", (90, 180, 230))), big=True)
            actor.facing_left = facing_left
            self.heroes.append((actor, x))

    def new_game(self):
        self.game.message = ""
        flow.begin_new_game(self.game)

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

    def update(self, dt):
        self.backdrop.update(dt)
        for actor, _ in self.heroes:
            actor.update(dt)       # keeps their idle animation playing

    def draw(self, surface):
        self.backdrop.draw(surface)
        for actor, x in self.heroes:
            image = actor.image()
            surface.blit(image, image.get_rect(midbottom=(x, HERO_FEET_Y)))
        super().draw(surface)      # the buttons, sliding in when the menu opens

    def draw_menu(self, surface):
        fonts = self.game.fonts
        cx = settings.SCREEN_W // 2
        self.glow.set_alpha(150 + round(80 * anim.pulse(0.4)), pygame.RLEACCEL)   # the light flickers slowly
        surface.blit(self.glow, self.glow.get_rect(center=(cx, self.logo_rect.centery + 10)))
        surface.blit(self.logo, self.logo_rect)
        widgets.text(surface, fonts["normal"], t("subtitle"), theme.OUTLINE, (cx + 2, self.subtitle_y + 2), "center")
        widgets.text(surface, fonts["normal"], t("subtitle"), theme.TEXT, (cx, self.subtitle_y), "center")
        surface.blit(self.frame_image, self.button_frame)
        mouse = pygame.mouse.get_pos()
        for i, button in enumerate(self.buttons):
            button.draw(surface, fonts["normal"], mouse, selected=(i == self.selected))
        widgets.text(surface, fonts["small"], t("menu_hint"), theme.TEXT_DIM, (cx, 690), "center")
        if self.game.message:
            widgets.text(surface, fonts["normal"], self.game.message, theme.BAD, (cx, MENU_TOP - 46), "center")
