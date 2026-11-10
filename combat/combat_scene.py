"""The fight screen (owner: B).

The rules live in combat/battle.py. This file only draws and reads input.
States:
  "choose"   - pick a move
  "question" - answer the question (multiple choice, tick-all, or typed)
  "message"  - show feedback; Enter runs the next step (self.next_step)
"""
import pygame

from combat.battle import Battle
from core import settings
from core.scene import Scene
from core.strings import t
from questions.engine import answer_text
from ui import widgets

NUMBER_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)
PANEL = pygame.Rect(40, 300, 1200, 400)


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

        self.state = "choose"
        self.moves = self.battle.moves()
        self.notice = ""        # e.g. "Not enough Rage."
        self.lines = []         # message lines: [(text, colour)]
        self.next_step = None   # what Enter does in the "message" state
        self.typed = ""         # typed answer so far
        self.ticked = set()     # ticked choice numbers (multi_select)
        self.elapsed = 0.0      # seconds spent on the current question
        self.ignore_text = False
        self.move_rects = []    # filled in by draw(), used for mouse clicks
        self.choice_rects = []

    # --- flow --------------------------------------------------------------
    def finish(self, won, fled=False):
        result = {"won": won, "fled": fled,
                  "xp": self.enemy.xp if won else 0, "gold": self.enemy.gold if won else 0, "loot": []}
        self.game.scenes.pop()
        self.on_end(result)

    def show_message(self, lines, next_step):
        self.state = "message"
        self.lines = lines
        self.next_step = next_step

    def back_to_choose(self):
        self.state = "choose"
        self.moves = self.battle.moves()
        self.notice = ""

    def pick_move(self, index):
        move = self.moves[index]
        if not move["affordable"]:
            self.notice = t("not_enough", resource=self.player.resource_name)
            return
        result = self.battle.choose_move(move["id"])
        if result.get("utility"):
            self.show_message([(t(f"effect_{result['effect']}"), settings.COLOR_HIGHLIGHT)], self.enemy_turn)
        else:
            self.start_question()

    def start_question(self):
        self.state = "question"
        self.typed = ""
        self.ticked = set()
        self.elapsed = 0.0
        self.ignore_text = True   # the key that picked the move must not appear in the text box

    def submit(self, given):
        out = self.battle.answer(given, self.elapsed)
        question = out["question"]
        lines = [(t("correct"), settings.COLOR_GOOD) if out["correct"] else (t("wrong"), settings.COLOR_BAD)]
        if not out["correct"]:
            lines.append((t("the_answer", answer=answer_text(question)), settings.COLOR_TEXT))
        if question.get("explanation"):
            lines.append((question["explanation"], settings.COLOR_DIM))
        if not out["done"]:
            self.show_message(lines, self.start_question)
            return
        lines.append((t("damage_dealt", damage=out["damage"]) if out["damage"] else t("miss"), settings.COLOR_HIGHLIGHT))
        self.show_message(lines, self.victory if self.battle.won else self.enemy_turn)

    def enemy_turn(self):
        out = self.battle.enemy_turn()
        if out["evaded"]:
            lines = [(t("enemy_misses", enemy=self.enemy.name), settings.COLOR_GOOD)]
        else:
            lines = [(t("enemy_hits", enemy=self.enemy.name, damage=out["damage"]), settings.COLOR_BAD)]
        if out["taunt"]:
            lines.append((t(out["taunt"]), settings.COLOR_HIGHLIGHT))
        self.show_message(lines, self.defeat if self.battle.lost else self.back_to_choose)

    def victory(self):
        self.show_message([(t("victory_fight", enemy=self.enemy.name), settings.COLOR_GOOD)],
                          lambda: self.finish(won=True))

    def defeat(self):
        self.show_message([(t("defeat_fight", enemy=self.enemy.name), settings.COLOR_BAD)],
                          lambda: self.finish(won=False))

    # --- input -------------------------------------------------------------
    def handle_event(self, event):
        if self.state == "choose":
            self._input_choose(event)
        elif self.state == "question":
            self._input_question(event)
        elif self.state == "message":
            if event.type == pygame.KEYDOWN and event.key in ENTER_KEYS + (pygame.K_SPACE,):
                self.next_step()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.next_step()

    def _input_choose(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in NUMBER_KEYS[: len(self.moves)]:
                self.pick_move(NUMBER_KEYS.index(event.key))
            elif event.key == pygame.K_ESCAPE and not self.enemy.boss:
                self.finish(won=False, fled=True)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.move_rects):
                if rect.collidepoint(event.pos):
                    self.pick_move(i)

    def _input_question(self, event):
        question = self.battle.question
        kind = question["type"]
        choices = question.get("choices", [])

        if kind == "typed":
            if event.type == pygame.TEXTINPUT and not self.ignore_text:
                self.typed += event.text
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.typed = self.typed[:-1]
                elif event.key in ENTER_KEYS and self.typed.strip():
                    self.submit(self.typed)
            return

        picked = None
        if event.type == pygame.KEYDOWN and event.key in NUMBER_KEYS[: len(choices)]:
            picked = NUMBER_KEYS.index(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            picked = next((i for i, r in enumerate(self.choice_rects) if r.collidepoint(event.pos)), None)

        if kind == "multi_select":
            if picked is not None:
                self.ticked ^= {picked}   # tick or untick
            elif event.type == pygame.KEYDOWN and event.key in ENTER_KEYS and self.ticked:
                self.submit([choices[i] for i in sorted(self.ticked)])
        elif picked is not None:          # multiple_choice
            self.submit(choices[picked])

    # --- every frame -------------------------------------------------------
    def update(self, dt):
        self.ignore_text = False
        if self.state == "question":
            self.elapsed += dt

    def draw(self, surface):
        f = self.game.fonts
        self._draw_fighters(surface, f)
        widgets.panel(surface, PANEL)
        if self.state == "choose":
            self._draw_choose(surface, f)
        elif self.state == "question":
            self._draw_question(surface, f)
        else:
            self._draw_message(surface, f)

    def _draw_fighters(self, surface, f):
        cx = settings.SCREEN_W // 2
        e = self.enemy
        name = f"{e.name}  ({t('boss_tag')})" if e.boss else e.name
        widgets.text(surface, f["big"], name, settings.COLOR_TEXT, (cx, 40), "center")
        widgets.bar(surface, (cx - 200, 70, 400, 22), e.hp, e.max_hp, settings.COLOR_HP)
        widgets.text(surface, f["small"], t("hp_label", hp=e.hp, max_hp=e.max_hp), settings.COLOR_TEXT,
                     (cx, 81), "center")
        size = 110 if e.boss else 80
        pygame.draw.rect(surface, e.color, (cx - size // 2, 105, size, size), border_radius=12)

        p = self.player
        widgets.text(surface, f["normal"], t("player_label", cls=p.class_name, level=p.level),
                     settings.COLOR_TEXT, (60, 226))
        widgets.bar(surface, (60, 262, 400, 18), p.hp, p.max_hp, settings.COLOR_HP)
        widgets.text(surface, f["small"], t("hp_label", hp=p.hp, max_hp=p.max_hp), settings.COLOR_TEXT,
                     (460, 232), "topright")
        widgets.bar(surface, (820, 262, 400, 18), p.resource, p.max_resource, settings.COLOR_RESOURCE)
        widgets.text(surface, f["small"], t("res_label", res=p.resource_name, r=p.resource, max_r=p.max_resource),
                     settings.COLOR_TEXT, (1220, 232), "topright")

    def _move_detail(self, move):
        if move["questions"] == 0:
            damage = t("move_no_question")
        elif move["questions"] > 1:
            damage = t("move_damage_ultimate", damage=move["damage"], bonus=move.get("bonus_damage", 0))
        else:
            damage = t("move_damage", damage=move["damage"])
        return t("move_detail", tier=t(f"tier_{move['tier']}"), damage=damage, cost=move["cost"])

    def _draw_choose(self, surface, f):
        x, y = PANEL.x + 24, PANEL.y + 18
        widgets.text(surface, f["normal"], t("combat_choose", n=len(self.moves)), settings.COLOR_TEXT, (x, y))
        self.move_rects = []
        y += 46
        for i, move in enumerate(self.moves):
            rect = pygame.Rect(x, y, PANEL.width - 48, 50)
            self.move_rects.append(rect)
            color = settings.COLOR_TEXT if move["affordable"] else settings.COLOR_DISABLED
            pygame.draw.rect(surface, (44, 38, 56), rect, border_radius=6)
            widgets.text(surface, f["normal"], t("move_line", number=i + 1, name=move["name"]), color,
                         (rect.x + 16, rect.centery), "midleft")
            widgets.text(surface, f["small"], self._move_detail(move), color,
                         (rect.right - 16, rect.centery), "midright")
            y += 58
        hint = t("combat_choose_hint_boss") if self.enemy.boss else t("combat_choose_hint")
        widgets.text(surface, f["small"], self.notice or hint,
                     settings.COLOR_BAD if self.notice else settings.COLOR_DIM, (x, PANEL.bottom - 34))

    def _draw_question(self, surface, f):
        q = self.battle.question
        move = self.battle.move
        x, y = PANEL.x + 24, PANEL.y + 18
        widgets.text(surface, f["small"], t("question_header", move=move["name"], topic=topic_name(q["topic"])),
                     settings.COLOR_DIM, (x, y))
        if move["questions"] > 1:
            done = move["questions"] - self.battle.remaining + 1
            widgets.text(surface, f["small"], t("question_count", i=done, n=move["questions"]),
                         settings.COLOR_HIGHLIGHT, (PANEL.centerx, y), "midtop")
        widgets.text(surface, f["small"], t("seconds", s=int(self.elapsed)), settings.COLOR_DIM,
                     (PANEL.right - 24, y), "topright")
        font = f["big"] if len(q["question"]) < 70 else f["normal"]   # long questions get smaller text
        y = widgets.wrapped(surface, font, q["question"], settings.COLOR_TEXT, (x, y + 36), PANEL.width - 48)

        self.choice_rects = []
        if q["type"] == "typed":
            box = pygame.Rect(x, y + 20, PANEL.width - 48, 56)
            pygame.draw.rect(surface, (50, 44, 64), box, border_radius=6)
            pygame.draw.rect(surface, settings.COLOR_HIGHLIGHT, box, width=2, border_radius=6)
            cursor = "|" if int(self.elapsed * 2) % 2 == 0 else ""
            widgets.text(surface, f["big"], self.typed + cursor, settings.COLOR_TEXT, (box.x + 14, box.centery), "midleft")
            hint = t("hint_typed")
        else:
            y += 8
            for i, choice in enumerate(q["choices"]):
                rect = pygame.Rect(x, y, PANEL.width - 48, 38)
                self.choice_rects.append(rect)
                ticked = q["type"] == "multi_select" and i in self.ticked
                pygame.draw.rect(surface, (70, 60, 90) if ticked else (44, 38, 56), rect, border_radius=6)
                mark = "[x] " if ticked else ("[  ] " if q["type"] == "multi_select" else "")
                widgets.text(surface, f["normal"], f"{i + 1}. {mark}{choice}",
                             settings.COLOR_HIGHLIGHT if ticked else settings.COLOR_TEXT,
                             (rect.x + 16, rect.centery), "midleft")
                y += 42
            n = len(q["choices"])
            hint = t("hint_multi", n=n) if q["type"] == "multi_select" else t("hint_choice", n=n)
        widgets.text(surface, f["small"], hint, settings.COLOR_DIM, (x, PANEL.bottom - 34))

    def _draw_message(self, surface, f):
        x, y = PANEL.x + 24, PANEL.y + 24
        for i, (line, color) in enumerate(self.lines):
            font = f["big"] if i == 0 else f["normal"]
            y = widgets.wrapped(surface, font, line, color, (x, y), PANEL.width - 48) + 8
        widgets.text(surface, f["small"], t("press_continue"), settings.COLOR_DIM, (x, PANEL.bottom - 34))
