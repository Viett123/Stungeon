"""The fight screen (owner: B).

The rules live in combat/battle.py. This file only draws and reads input.
States:
  "choose"   - pick a move from the hotbar
  "question" - answer the question (multiple choice, tick-all, or typed)
  "message"  - show feedback; Enter runs the next step (self.next_step)
"""
import pygame

from combat.battle import Battle
from core.scene import Scene
from core.strings import t
from dungeon.actor import make_actor
from questions.engine import answer_text
from systems.loot import roll_loot
from ui import hud, move_info, theme, widgets
from ui.button import Button
from ui.hotbar import Hotbar
from ui.text_input import TextInput

NUMBER_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)

ENEMY_PANEL = pygame.Rect(410, 12, 460, 212)
PLAYER_ART = pygame.Rect(938, 12, 202, 212)     # the player's picture, right of the enemy
HURT_SECONDS = 0.6
CONTENT = pygame.Rect(140, 236, 1000, 384)     # the big panel: move details, question or feedback
INSIDE = theme.inner(CONTENT)
CHOICE_HEIGHT = 36
CHOICE_GAP = 4


def topic_name(topic):
    return topic.replace("_", " ")


class CombatScene(Scene):
    def __init__(self, game, player, enemy, on_end):
        super().__init__(game)
        run = game.run_state
        self.player = player
        self.enemy = enemy
        self.on_end = on_end   # called once with the result dict, see finish()
        self.battle = Battle(player, enemy, run.engine, run.floor_number, habits=run.habits, rng=run.rng)
        # In a fight both fighters are drawn big and animated. They stand still, so the
        # tile they are "on" does not matter; the player faces left, towards the enemy.
        self.enemy_actor = make_actor(f"enemy_{enemy.id}", (0, 0), enemy.color, big=True)
        self.player_actor = make_actor(f"player_{player.class_id}", (0, 0), player.color, big=True)
        self.player_actor.facing_left = True
        self.hurt = 0.0         # seconds left to show the player's "hit" picture

        self.state = "choose"
        self.moves = []
        self.selected = 0       # which hotbar slot is highlighted
        self.hotbar = Hotbar()
        self.refresh_moves()
        self.notice = ""        # e.g. "Not enough Rage."
        self.lines = []         # message lines: [(text, colour)]
        self.next_step = None   # what Enter does in the "message" state
        self.input = TextInput()
        self.ticked = set()     # ticked choice numbers (multi_select)
        self.elapsed = 0.0      # seconds spent on the current question
        self.ignore_text = False
        self.question_font = game.fonts["big"]
        self.question_lines = []
        self.choice_buttons = []

    # --- flow --------------------------------------------------------------
    def finish(self, won, fled=False):
        loot = roll_loot(self.enemy.loot_table, self.game.run_state.rng) if won else []
        result = {"won": won, "fled": fled,
                  "xp": self.enemy.xp if won else 0, "gold": self.enemy.gold if won else 0, "loot": loot}
        self.game.scenes.pop()
        self.on_end(result)

    def refresh_moves(self):
        """Ask the battle which moves can be used now and show them in the hotbar."""
        self.moves = self.battle.moves()
        self.selected = min(self.selected, len(self.moves) - 1)
        self.hotbar.set_entries(
            move_info.hotbar_entries(self.moves, self.player.resource_name, self.game.fonts["small"]))

    def show_message(self, lines, next_step):
        self.state = "message"
        self.lines = lines
        self.next_step = next_step

    def back_to_choose(self):
        self.state = "choose"
        self.refresh_moves()
        self.notice = ""

    def pick_move(self, index):
        self.selected = index
        move = self.moves[index]
        if not move["affordable"]:
            self.notice = t("not_enough", resource=self.player.resource_name)
            return
        result = self.battle.choose_move(move["id"])
        if result.get("utility"):
            # TODO(B): once combat/effects.py has real effects, show what the move did here.
            self.show_message([(t("utility_used", move=move["name"]), theme.GOLD)], self.enemy_turn)
        else:
            self.start_question()

    def start_question(self):
        self.state = "question"
        self.input.clear()
        self.ticked = set()
        self.elapsed = 0.0
        self.ignore_text = True   # the key that picked the move must not appear in the text box
        self.layout_question()

    def layout_question(self):
        """Work out where the question text and its answers go. Done once per question, not per frame."""
        question = self.battle.question
        fonts = self.game.fonts
        # Long questions get smaller text so they still fit.
        self.question_font = fonts["big"] if len(question["question"]) < 60 else fonts["normal"]
        self.question_lines = widgets.wrap(self.question_font, question["question"], INSIDE.width)
        y = INSIDE.y + 30 + len(self.question_lines) * (self.question_font.get_height() + 6) + 8
        self.choice_buttons = []
        if question["type"] == "typed":
            self.input.rect = pygame.Rect(INSIDE.x, y + 8, INSIDE.width, 52)
            return
        for choice in question["choices"]:
            self.choice_buttons.append(Button((INSIDE.x, y, INSIDE.width, CHOICE_HEIGHT), choice))
            y += CHOICE_HEIGHT + CHOICE_GAP

    def submit(self, given):
        out = self.battle.answer(given, self.elapsed)
        question = out["question"]
        lines = [(t("correct"), theme.GOOD) if out["correct"] else (t("wrong"), theme.BAD)]
        if not out["correct"]:
            lines.append((t("the_answer", answer=answer_text(question)), theme.TEXT))
        if question.get("explanation"):
            lines.append((question["explanation"], theme.TEXT_DIM))
        if not out["done"]:
            self.show_message(lines, self.start_question)
            return
        lines.append((t("damage_dealt", damage=out["damage"]) if out["damage"] else t("miss"), theme.GOLD))
        self.show_message(lines, self.victory if self.battle.won else self.enemy_turn)

    def enemy_turn(self):
        out = self.battle.enemy_turn()
        if out["damage"] == 0:   # e.g. an effect cancelled the attack
            lines = [(t("enemy_misses", enemy=self.enemy.name), theme.GOOD)]
        else:
            lines = [(t("enemy_hits", enemy=self.enemy.name, damage=out["damage"]), theme.BAD)]
            self.hurt = HURT_SECONDS
        if out["taunt"]:
            lines.append((t(out["taunt"]), theme.GOLD))
        self.show_message(lines, self.defeat if self.battle.lost else self.back_to_choose)

    def victory(self):
        self.show_message([(t("victory_fight", enemy=self.enemy.name), theme.GOOD)],
                          lambda: self.finish(won=True))

    def defeat(self):
        self.show_message([(t("defeat_fight", enemy=self.enemy.name), theme.BAD)],
                          lambda: self.finish(won=False))

    # --- input -------------------------------------------------------------
    def handle_event(self, event):
        if self.state == "choose":
            self.input_choose(event)
        elif self.state == "question":
            self.input_question(event)
        elif event.type == pygame.KEYDOWN and event.key in ENTER_KEYS + (pygame.K_SPACE,):
            self.next_step()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.next_step()

    def input_choose(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in NUMBER_KEYS[: len(self.moves)]:
                self.pick_move(NUMBER_KEYS.index(event.key))
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(self.moves)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(self.moves)
            elif event.key in ENTER_KEYS:
                self.pick_move(self.selected)
            elif event.key == pygame.K_ESCAPE and not self.enemy.boss:
                self.finish(won=False, fled=True)
        elif event.type == pygame.MOUSEMOTION:
            hovered = self.hotbar.index_at(event.pos)
            if hovered is not None:
                self.selected = hovered   # pointing at a slot shows its details in the panel
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self.hotbar.index_at(event.pos)
            if clicked is not None:
                self.pick_move(clicked)

    def input_question(self, event):
        question = self.battle.question
        if question["type"] == "typed":
            self.input_typed(event)
            return
        choices = question["choices"]
        picked = None
        if event.type == pygame.KEYDOWN and event.key in NUMBER_KEYS[: len(choices)]:
            picked = NUMBER_KEYS.index(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            picked = next((i for i, b in enumerate(self.choice_buttons) if b.hit(event.pos)), None)

        if question["type"] == "multi_select":
            if picked is not None:
                self.ticked ^= {picked}   # tick or untick
            elif event.type == pygame.KEYDOWN and event.key in ENTER_KEYS and self.ticked:
                self.submit([choices[i] for i in sorted(self.ticked)])
        elif picked is not None:          # multiple_choice
            self.submit(choices[picked])

    def input_typed(self, event):
        if event.type == pygame.TEXTINPUT and self.ignore_text:
            return
        if event.type == pygame.KEYDOWN and event.key in ENTER_KEYS:
            if self.input.text.strip():
                self.submit(self.input.text)
            return
        self.input.handle_event(event)

    # --- every frame -------------------------------------------------------
    def update(self, dt):
        self.ignore_text = False
        self.input.update(dt)
        self.enemy_actor.update(dt)
        self.player_actor.update(dt)
        self.hurt = max(0.0, self.hurt - dt)
        if self.state == "question":
            self.elapsed += dt

    def draw(self, surface):
        fonts = self.game.fonts
        hud.draw_player_panel(surface, fonts, self.player)
        self.draw_enemy(surface, fonts)
        self.draw_player(surface)
        theme.draw_frame(surface, CONTENT)
        if self.state == "choose":
            self.draw_choose(surface, fonts)
        elif self.state == "question":
            self.draw_question(surface, fonts)
        else:
            self.draw_message(surface, fonts)
        choosing = self.state == "choose"
        self.hotbar.draw(surface, fonts, pygame.mouse.get_pos(),
                         selected=self.selected if choosing else None, active=choosing)

    def draw_enemy(self, surface, fonts):
        inside = theme.draw_frame(surface, ENEMY_PANEL)
        enemy = self.enemy
        name = f"{enemy.name}  ({t('boss_tag')})" if enemy.boss else enemy.name
        widgets.text(surface, fonts["normal"], name, theme.GOLD, (inside.centerx, inside.y), "midtop")
        widgets.bar(surface, (inside.x, inside.y + 30, inside.width, 22), enemy.hp, enemy.max_hp,
                    theme.HP, theme.HP_BACK, t("hp_label", hp=enemy.hp, max_hp=enemy.max_hp), fonts["small"])
        image = self.enemy_actor.image()
        surface.blit(image, image.get_rect(midbottom=(inside.centerx, inside.bottom)))

    def draw_player(self, surface):
        """The player's picture in its own small panel; it shows the "hit" frame right after being hurt."""
        inside = theme.draw_frame(surface, PLAYER_ART)
        image = self.player_actor.image("hit" if self.hurt > 0 else None)
        surface.blit(image, image.get_rect(midbottom=(inside.centerx, inside.bottom)))

    def hint(self, surface, fonts, string, color=theme.TEXT_DIM):
        widgets.text(surface, fonts["small"], string, color, INSIDE.bottomleft, "bottomleft")

    def draw_choose(self, surface, fonts):
        widgets.text(surface, fonts["small"], t("combat_choose"), theme.TEXT_DIM, INSIDE.topleft)
        y = INSIDE.y + 40
        lines = move_info.move_lines(self.moves[self.selected], self.player.resource_name)
        for i, (line, color) in enumerate(lines):
            font = fonts["big"] if i == 0 else fonts["normal"]
            widgets.text(surface, font, line, color, (INSIDE.x, y))
            y += font.get_height() + 12
        if self.notice:
            self.hint(surface, fonts, self.notice, theme.BAD)
        else:
            key = "combat_choose_hint_boss" if self.enemy.boss else "combat_choose_hint"
            self.hint(surface, fonts, t(key, n=len(self.moves)))

    def draw_question(self, surface, fonts):
        question = self.battle.question
        move = self.battle.move
        small = fonts["small"]
        widgets.text(surface, small, t("question_header", move=move["name"], topic=topic_name(question["topic"])),
                     theme.TEXT_DIM, INSIDE.topleft)
        if move["questions"] > 1:
            number = move["questions"] - self.battle.remaining + 1
            widgets.text(surface, small, t("question_count", i=number, n=move["questions"]),
                         theme.GOLD, (INSIDE.centerx, INSIDE.y), "midtop")
        widgets.text(surface, small, t("seconds", s=int(self.elapsed)), theme.TEXT_DIM, INSIDE.topright, "topright")

        y = INSIDE.y + 30
        for line in self.question_lines:
            widgets.text(surface, self.question_font, line, theme.TEXT, (INSIDE.x, y))
            y += self.question_font.get_height() + 6

        if question["type"] == "typed":
            self.input.draw(surface, fonts["big"])
            self.hint(surface, fonts, t("hint_typed"))
            return
        multi = question["type"] == "multi_select"
        mouse = pygame.mouse.get_pos()
        for i, button in enumerate(self.choice_buttons):
            ticked = multi and i in self.ticked
            mark = ("[x] " if ticked else "[  ] ") if multi else ""
            button.label = f"{i + 1}. {mark}{question['choices'][i]}"
            button.draw(surface, fonts["normal"], mouse, selected=ticked)
        count = len(self.choice_buttons)
        self.hint(surface, fonts, t("hint_multi", n=count) if multi else t("hint_choice", n=count))

    def draw_message(self, surface, fonts):
        y = INSIDE.y + 6
        for i, (line, color) in enumerate(self.lines):
            font = fonts["big"] if i == 0 else fonts["normal"]
            y = widgets.wrapped(surface, font, line, color, (INSIDE.x, y), INSIDE.width) + 8
        self.hint(surface, fonts, t("press_continue"))
