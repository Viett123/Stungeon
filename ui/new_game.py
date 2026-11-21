"""The new-game screens: name your hero, choose a dungeon, then the welcome and level screen (owner: B).

The order of the screens is decided in core/flow.py:
    name -> class -> dungeon -> welcome + level -> floor 1
Each screen only tells flow what the player picked; Esc goes back one screen.
What has been picked so far is kept in game.new_game (a dict).
"""
import unicodedata

import pygame

from core import flow, settings
from core.scene import Scene
from core.strings import t
from systems import dungeons
from ui import anim, theme, widgets
from ui.backdrop import Backdrop
from ui.text_input import TextInput

NAME_LENGTH = 14            # long enough for most names, short enough for the HUD panel
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)
LEFT_KEYS = (pygame.K_LEFT, pygame.K_a)
RIGHT_KEYS = (pygame.K_RIGHT, pygame.K_d)
CARD_TOP = 250


NO_GLYPH = ""          # a character no font draws: what a missing letter looks like (an empty box)


def _can_draw(char, font):
    """True if the font has a real picture for this character, not the empty box.

    font.metrics() is not enough: it gives the box's size for missing letters.
    So the character is drawn and compared with how a surely missing one is drawn.
    """
    picture = pygame.image.tobytes(font.render(char, False, (255, 255, 255)), "RGBA")
    box = pygame.image.tobytes(font.render(NO_GLYPH, False, (255, 255, 255)), "RGBA")
    return picture != box


def drawable_letter(char, font):
    """The character itself if the font can draw it, otherwise the closest letter it can draw, or "".

    A letter with accents can be split into the plain letter plus its accent marks
    (unicodedata "NFD"). The marks are taken off one at a time from the end until the
    font can draw what is left: "ệ" (e + hat + dot) becomes "ê", and if needed "e".
    """
    if char.isspace() or _can_draw(char, font):
        return char
    parts = unicodedata.normalize("NFD", char)
    while len(parts) > 1:
        parts = parts[:-1]
        simpler = unicodedata.normalize("NFC", parts)
        if _can_draw(simpler, font):
            return simpler
    return ""


def drawable_text(text, font):
    return "".join(drawable_letter(char, font) for char in text)


def clean_name(text, font):
    """The typed name with only letters the font can draw, without extra spaces, cut to NAME_LENGTH."""
    return " ".join(drawable_text(text, font).split())[:NAME_LENGTH]


def draw_lock(surface, center, color):
    """A small padlock drawn with rectangles, for things that are not ready yet."""
    x, y = center
    pygame.draw.rect(surface, color, (x - 9, y - 16, 18, 16), width=4, border_radius=8)
    pygame.draw.rect(surface, color, (x - 13, y - 4, 26, 20), border_radius=3)
    pygame.draw.rect(surface, theme.OUTLINE, (x - 2, y + 2, 4, 8))


def draw_gate(surface, rect, color, open_):
    """A dungeon doorway: a stone arch, dark inside, lit in the dungeon's colour if it is open."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, theme.STONE_LIGHT, rect, border_top_left_radius=rect.width // 2,
                     border_top_right_radius=rect.width // 2)
    inside = rect.inflate(-16, -12).move(0, 6)
    glow = anim.blend(theme.OUTLINE, color, 0.25 + 0.2 * anim.pulse(0.6)) if open_ else theme.OUTLINE
    pygame.draw.rect(surface, glow, inside, border_top_left_radius=inside.width // 2,
                     border_top_right_radius=inside.width // 2)
    for i in range(1, 4):                              # stone joints on the arch
        y = rect.y + rect.height * i // 4
        pygame.draw.line(surface, theme.STONE, (rect.x, y), (inside.x, y), 2)
        pygame.draw.line(surface, theme.STONE, (inside.right, y), (rect.right, y), 2)


class NewGameScreen(Scene):
    """What the three screens share: the dungeon backdrop, a title, a hint and a message line."""

    def __init__(self, game):
        super().__init__(game)
        self.backdrop = Backdrop()
        self.message = ""

    def update(self, dt):
        self.backdrop.update(dt)

    def draw_common(self, surface, title, hint):
        fonts = self.game.fonts
        cx = settings.SCREEN_W // 2
        self.backdrop.draw(surface)
        widgets.text(surface, fonts["big"], title, theme.OUTLINE, (cx + 3, 193), "center")   # shadow
        widgets.text(surface, fonts["big"], title, theme.GOLD, (cx, 190), "center")
        widgets.text(surface, fonts["small"], hint, theme.TEXT_DIM, (cx, 690), "center")
        if self.message:
            widgets.text(surface, fonts["normal"], self.message, theme.BAD, (cx, 650), "center")


# --- 1. name -----------------------------------------------------------------
class NameScene(NewGameScreen):
    def __init__(self, game):
        super().__init__(game)
        self.input = TextInput(((settings.SCREEN_W - 480) // 2, 330, 480, 60), max_length=NAME_LENGTH)
        self.input.text = game.new_game.get("name", "")      # coming back with Esc keeps the name

    def confirm(self):
        name = clean_name(self.input.text, self.game.fonts["big"]) or t("default_hero_name")
        flow.name_chosen(self.game, name)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in ENTER_KEYS:
            self.confirm()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.go_to_title()
        else:
            self.input.handle_event(event)
            # Swap letters the font cannot draw straight away, so the box never shows an empty square.
            self.input.text = drawable_text(self.input.text, self.game.fonts["big"])

    def update(self, dt):
        super().update(dt)
        self.input.update(dt)

    def draw(self, surface):
        self.draw_common(surface, t("name_title"), t("name_hint"))
        frame = pygame.Rect(self.input.rect.inflate(120, 150)).move(0, 20)
        theme.draw_frame(surface, frame)
        widgets.text(surface, self.game.fonts["normal"], t("name_prompt"), theme.TEXT,
                     (frame.centerx, frame.y + 34), "center")
        self.input.draw(surface, self.game.fonts["big"])
        widgets.text(surface, self.game.fonts["small"], t("name_default", name=t("default_hero_name")),
                     theme.TEXT_DIM, (frame.centerx, frame.bottom - 30), "center")


# --- card screens (dungeon, level) ---------------------------------------------
class CardScreen(NewGameScreen):
    """A row of cards; Left/Right (or the number keys, or the mouse) choose, Enter goes in."""

    CARD_W, CARD_H, GAP = 260, 330, 26

    def __init__(self, game, count):
        super().__init__(game)
        self.count = count
        self.selected = 0
        width = count * self.CARD_W + (count - 1) * self.GAP
        left = (settings.SCREEN_W - width) // 2
        self.cards = [pygame.Rect(left + i * (self.CARD_W + self.GAP), CARD_TOP, self.CARD_W, self.CARD_H)
                      for i in range(count)]

    def choose(self, index):
        """Enter (or a click on the selected card). Each screen says what happens."""

    def back(self):
        """Esc. Each screen says where it goes back to."""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in LEFT_KEYS:
                self.selected = (self.selected - 1) % self.count
            elif event.key in RIGHT_KEYS:
                self.selected = (self.selected + 1) % self.count
            elif pygame.K_1 <= event.key < pygame.K_1 + self.count:
                self.selected = event.key - pygame.K_1
            elif event.key in ENTER_KEYS:
                self.choose(self.selected)
            elif event.key == pygame.K_ESCAPE:
                self.back()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.cards):
                if rect.collidepoint(event.pos):
                    if i == self.selected:
                        self.choose(i)
                    self.selected = i


# --- 2. dungeon (after the class screen) -------------------------------------------
class DungeonSelectScene(CardScreen):
    def __init__(self, game):
        self.dungeons = dungeons.all_dungeons()
        super().__init__(game, len(self.dungeons))
        self.selected = next((i for i, d in enumerate(self.dungeons) if d["available"]), 0)

    def choose(self, index):
        dungeon = self.dungeons[index]
        if not dungeon["available"]:
            self.message = t("dungeon_locked", dungeon=t(f"dungeon_{dungeon['id']}"))
            return
        flow.dungeon_chosen(self.game, dungeon["id"])

    def back(self):
        flow.show_class_select(self.game)

    def draw(self, surface):
        self.draw_common(surface, t("dungeon_title"), t("card_hint", n=self.count))
        fonts = self.game.fonts
        for i, (dungeon, rect) in enumerate(zip(self.dungeons, self.cards)):
            open_ = dungeon["available"]
            color = tuple(dungeon["color"])
            theme.draw_frame(surface, rect, highlight=(i == self.selected))
            draw_gate(surface, (rect.centerx - 50, rect.y + 34, 100, 120), color, open_)
            if not open_:
                draw_lock(surface, (rect.centerx, rect.y + 104), theme.DISABLED)
            name_color = theme.GOLD if open_ else theme.DISABLED
            widgets.text(surface, fonts["normal"], t(f"dungeon_{dungeon['id']}"), name_color,
                         (rect.centerx, rect.y + 180), "center")
            widgets.wrapped(surface, fonts["small"], t(f"dungeon_{dungeon['id']}_text"),
                            theme.TEXT_DIM if open_ else theme.DISABLED, (rect.x + 22, rect.y + 206), rect.width - 44)
            status = t("dungeon_open") if open_ else t("in_development")
            widgets.text(surface, fonts["small"], status, theme.GOOD if open_ else theme.DISABLED,
                         (rect.centerx, rect.bottom - 30), "center")


# --- 3. welcome + level -------------------------------------------------------
class LevelSelectScene(CardScreen):
    def __init__(self, game, subject):
        self.subject = subject
        self.levels = [entry["id"] for entry in dungeons.get_dungeon(subject)["levels"]]
        # Read once here: the counts come from the bank files, which are too big to read every frame.
        self.counts = {level: dungeons.question_count(subject, level) for level in self.levels}
        self.playable = {level: dungeons.is_playable(subject, level) for level in self.levels}
        super().__init__(game, len(self.levels))
        self.cards = [rect.move(0, 40) for rect in self.cards]
        self.selected = next((i for i, level in enumerate(self.levels) if self.playable[level]), 0)

    def choose(self, index):
        level = self.levels[index]
        if not self.playable[level]:
            self.message = t("level_locked", level=level)
            return
        flow.level_chosen(self.game, level)

    def back(self):
        flow.show_dungeon_select(self.game)

    def draw(self, surface):
        dungeon_name = t(f"dungeon_{self.subject}")
        name = self.game.new_game.get("name", t("default_hero_name"))
        self.draw_common(surface, t("welcome_title", name=name, dungeon=dungeon_name), t("card_hint", n=self.count))
        fonts = self.game.fonts
        cx = settings.SCREEN_W // 2
        widgets.text(surface, fonts["normal"], t(f"welcome_{self.subject}"), theme.TEXT, (cx, 236), "center")
        widgets.text(surface, fonts["normal"], t("level_title"), theme.TEXT_DIM, (cx, 270), "center")
        for i, (level, rect) in enumerate(zip(self.levels, self.cards)):
            open_ = self.playable[level]
            theme.draw_frame(surface, rect, highlight=(i == self.selected))
            widgets.text(surface, fonts["title"], level, theme.GOLD if open_ else theme.DISABLED,
                         (rect.centerx, rect.y + 70), "center")
            if not open_:
                draw_lock(surface, (rect.right - 36, rect.y + 40), theme.DISABLED)
            widgets.wrapped(surface, fonts["small"], t(f"level_{self.subject}_{level}_text"),
                            theme.TEXT_DIM if open_ else theme.DISABLED, (rect.x + 22, rect.y + 130), rect.width - 44)
            if open_:
                status, color = t("level_questions", n=self.counts[level]), theme.GOOD
            else:
                status, color = t("level_coming_soon"), theme.DISABLED
            widgets.text(surface, fonts["small"], status, color, (rect.centerx, rect.bottom - 30), "center")
