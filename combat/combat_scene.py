"""The fight screen (owner: B).

The rules live in combat/battle.py. This file only draws and reads input.
States:
  "choose"   - pick a move from the hotbar
  "question" - answer the question (multiple choice, tick-all, or typed)
  "message"  - show feedback; Enter runs the next step (self.next_step)
"""
import math

import pygame

from combat import effects
from combat.battle import Battle
from combat.skill_looks import AURA_SECONDS, SkillLook
from core import assets, settings, sound
from core.scene import Scene
from core.strings import t
from dungeon.actor import make_actor
from dungeon.weapon import IMPACT, STRIKE_START, held_weapon
from questions.engine import answer_text
from systems import inventory, items
from systems.loot import roll_loot
from ui import anim, hud, learning_panel, move_info, theme, topic_names, widgets
from ui.anim import FloatingText, Shake, Trail
from ui.button import Button
from ui.hotbar import Hotbar
from ui.text_input import TextInput

NUMBER_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)

ENEMY_PANEL = pygame.Rect(410, 12, 460, 212)
PLAYER_ART = pygame.Rect(938, 12, 202, 212)     # the player's picture, right of the enemy
HURT_SECONDS = 0.6
HIT_PAUSE = 0.07            # seconds everything freezes when a hit lands
FLASH_SECONDS = 0.12        # seconds the enemy is drawn white after a hit
USE_SECONDS = 0.6           # how long the use-an-item animation plays
DIE_SECONDS = 0.7           # how long the defeat animation takes (its last picture then stays)
SPARK_SECONDS = 0.3         # how long the hit sparks stay on the enemy
WIND_UP_PIXELS = 6          # how far the player leans back before striking
LUNGE_PIXELS = 18           # how far a melee fighter jumps towards the enemy
KNOCKBACK_PIXELS = 10       # how far the player is pushed back when hurt
HOP_PIXELS = 10             # how high the player hops when using an item
CRIT_LIFT = -42             # "CRIT!" starts this far BELOW the damage number (above it, it would cover the HP bar)
RED_FLASH_SECONDS = 0.3     # the screen flashes red this long when the player is hit
RED_FLASH_ALPHA = 110       # how strong the red is at the start (0 = none, 255 = solid red)
RED = (200, 30, 30)
STREAK_POPUP_FROM = 2       # "2 in a row!" is the first streak pop-up
STREAK_POPUP_AT = PLAYER_ART.move(-120, 0)   # over the player, a bit to the left so the big text fits on screen
TAUNT_SECONDS = 4.0         # how long the enemy's speech bubble stays
TAUNT_BUBBLE_WIDTH = 190   # fits in the empty space left of the enemy
ATTACK_SECONDS = 0.6      # how long the weapon swing and the hit sparks last
FIGHTER_SCALE = settings.TILE_SCALE + 1   # fighters are drawn 4 times the art size, like bosses
CONTENT = pygame.Rect(140, 236, 1000, 384)     # the big panel: move details, question or feedback
INSIDE = theme.inner(CONTENT)
CHOICE_HEIGHT = 42          # one answer row: room for the "answer" font (34 px)
QUESTION_MAX_LINES = 2      # a longer question switches to the smaller question font
CHOICE_GAP = 4


def topic_name(topic):
    return topic_names.label(topic)


def is_weak_hit(results):
    """True when only some of a move's answers were right (e.g. 1 of an Ultimate's 3): it still hits,
    but much weaker. All wrong is a miss, not a weak hit. (Not judged by the damage number: the last
    blow on an almost dead enemy is small too, and should still feel good.)"""
    return any(results) and not all(results)


def utility_lines(move):
    """The message after a utility move: "You use War Cry." and, under it, what the move does."""
    lines = [(t("utility_used", move=move["name"]), theme.GOLD)]
    hint = effects.UTILITY_HINTS.get(move["id"])
    if hint:
        lines.append((t(hint), theme.TEXT))
    return lines


class CombatScene(Scene):
    def __init__(self, game, player, enemy, on_end):
        super().__init__(game)
        run = game.run_state
        self.player = player
        self.enemy = enemy
        self.on_end = on_end   # called once with the result dict, see finish()
        self.music = "boss" if enemy.boss else "fight"      # core/sound.py plays it while this screen is on top
        self.battle = Battle(player, enemy, run.engine, run.floor_number, habits=run.habits, rng=run.rng)
        # In a fight both fighters are drawn big and animated. They stand still, so the
        # tile they are "on" does not matter; the player faces left, towards the enemy.
        self.enemy_actor = make_actor(f"enemy_{enemy.id}", (0, 0), enemy.color, big=not enemy.large_art)
        self.enemy_name = t("elite_name", name=enemy.name) if enemy.elite else enemy.name
        self.player_actor = make_actor(f"player_{player.class_id}", (0, 0), player.color, big=True)
        self.player_actor.facing_left = True
        self.hurt = 0.0         # seconds left to show the player's "hit" picture
        self.weapon = held_weapon(player, FIGHTER_SCALE)
        self.enemy_trail = Trail(enemy.hp)
        self.attack = 0.0       # seconds left of the player's attack (weapon swing + sparks on the enemy)
        self.sparks = assets.load_frames("effect_hit", FIGHTER_SCALE)
        self.floating = []      # damage numbers that rise and fade
        self.using = 0.0        # seconds left of the "use an item" animation
        self.pending_damage = 0 # damage of an attack that is on its way and has not landed yet
        self.pending_crit = False   # show "CRIT!" when that attack lands
        self.spark = 0.0        # seconds left of the hit sparks on the enemy
        self.enemy_center = ENEMY_PANEL.center     # where arrows and bolts fly to (set when the enemy is drawn)
        self.player_hand = PLAYER_ART.center       # where the player's skills start (set when the player is drawn)
        self.player_center = PLAYER_ART.center     # the middle of the player's picture, for rings
        self.skill = None       # the look of the move being used (combat/skill_looks.py), or None
        self.dying = None       # seconds since the player was defeated (None while alive)
        # "Juice": small effects that make a hit feel like a hit.
        self.shake = Shake()    # the whole screen shakes for a moment
        self.freeze = 0.0       # seconds everything stands still right after a hit
        self.flash = 0.0        # seconds the enemy is drawn all white
        self.white = {}         # white copies of the enemy's pictures, made the first time each is needed
        self.red_flash = 0.0    # seconds left of the red flash over the screen (the player was hit)
        self.red_layer = pygame.Surface((settings.SCREEN_W, settings.SCREEN_H))   # made once, see draw_scene
        self.red_layer.fill(RED)
        self.pending_weak = False   # the attack on its way is a weak hit: small grey number
        # What the player learned in this fight (ui/learning_panel.py), shown when it ends.
        self.learned_before = {}    # {topic: mastery just before its first question in this fight}
        self.learning = []          # [(topic, before, after)], worked out once when the fight ends
        self.learning_shown_at = 0.0
        self.buffer = pygame.Surface((settings.SCREEN_W, settings.SCREEN_H))   # used only while shaking
        # Items that can be used in this fight (the "items" state).
        self.item_ids = []
        self.item_buttons = []
        self.item_selected = 0
        self.items_button = Button((INSIDE.right - 170, INSIDE.bottom - 44, 170, 40), t("items_button"))

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
        self.question_font = game.fonts["question"]
        self.question_lines = []
        self.choice_buttons = []
        # Taunts (ai/habits.py): a speech bubble over the enemy, so they are hard to miss.
        self.taunt_bubble = None    # the bubble picture, made once per taunt
        self.taunt_time = 0.0       # seconds left to show it
        self.show_taunt(self.battle.start())     # the enemy may greet you with what it noticed before

    def float_text(self, string, color, panel, lift=0, font=None):
        """Show a rising, fading text over one of the fighter panels. lift: start this many pixels higher (negative = lower).
        font: how big it is (default "big")."""
        font = font or self.game.fonts["big"]
        self.floating.append(FloatingText(font, string, color, (panel.centerx + 60, panel.centery - lift)))

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
            # Only a picture: what the move really does is decided in combat/effects.py.
            self.skill = SkillLook(move["id"], self.player_center, self.player_center, AURA_SECONDS)
            sound.play(sound.skill_sound("aura"))
            self.show_message(utility_lines(move), self.enemy_turn)
        else:
            self.start_question()

    # --- items ---------------------------------------------------------------
    def open_items(self):
        """Show the consumables in the bag as a list. Each kind is listed once, with how many there are."""
        self.item_ids = []
        for item_id in self.player.inventory:
            if item_id not in self.item_ids and items.get_item(item_id)["kind"] == "consumable":
                self.item_ids.append(item_id)
        if not self.item_ids:
            self.notice = t("items_none")
            return
        self.state = "items"
        self.notice = ""
        self.item_selected = min(self.item_selected, len(self.item_ids) - 1)
        self.item_buttons = [Button((INSIDE.x, INSIDE.y + 44 + i * 46, 520, 40), "")
                             for i in range(len(self.item_ids))]

    def use_item(self, index):
        item = items.get_item(self.item_ids[index])
        if not inventory.use_item(self.player, item["id"]):
            self.notice = t("item_no_effect", item=item["name"])     # e.g. a potion at full HP: keep it
            return
        self.using = USE_SECONDS
        sound.play("potion")
        lines = [(t("item_used", item=item["name"]), theme.GOLD)]
        # TODO(B): whether an item costs the turn is decided in combat/effects.py.
        self.show_message(lines, self.enemy_turn if effects.item_costs_turn(self.battle) else self.back_to_choose)

    def input_items(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.item_selected = (self.item_selected - 1) % len(self.item_ids)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.item_selected = (self.item_selected + 1) % len(self.item_ids)
            elif event.key in ENTER_KEYS:
                self.use_item(self.item_selected)
            elif event.key in (pygame.K_ESCAPE, pygame.K_i):
                self.back_to_choose()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.item_buttons):
                if button.hit(event.pos):
                    self.use_item(i)
                    return

    def draw_items(self, surface, fonts):
        widgets.text(surface, fonts["small"], t("items_title"), theme.TEXT_DIM, INSIDE.topleft)
        mouse = pygame.mouse.get_pos()
        for i, (button, item_id) in enumerate(zip(self.item_buttons, self.item_ids)):
            item = items.get_item(item_id)
            button.label = t("item_line", name=item["name"], n=self.player.inventory.count(item_id))
            button.draw(surface, fonts["normal"], mouse, selected=(i == self.item_selected))
        selected = items.get_item(self.item_ids[self.item_selected])
        widgets.wrapped(surface, fonts["small"], selected["text"], theme.TEXT, (INSIDE.x + 560, INSIDE.y + 52),
                        INSIDE.right - INSIDE.x - 560)
        if self.notice:
            self.hint(surface, fonts, self.notice, theme.BAD)
        else:
            self.hint(surface, fonts, t("items_hint"))

    def start_question(self):
        self.state = "question"
        self.input.clear()
        self.ticked = set()
        self.elapsed = 0.0
        self.ignore_text = True   # the key that picked the move must not appear in the text box
        topic = self.battle.question.get("topic")
        tracker = self.game.run_state.tracker
        if topic and topic not in self.learned_before:
            self.learned_before[topic] = tracker.mastery(topic)     # noted before the answer changes it
        self.layout_question()

    def layout_question(self):
        """Work out where the question text and its answers go. Done once per question, not per frame."""
        question = self.battle.question
        fonts = self.game.fonts
        # Big, clear text. Only a question that needs more than 2 lines gets the smaller size,
        # so even the longest question and 5 answers fit above the hint.
        self.question_font = fonts["question"]
        self.question_lines = widgets.wrap(self.question_font, question["question"], INSIDE.width)
        if len(self.question_lines) > QUESTION_MAX_LINES:
            self.question_font = fonts["question_small"]
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
        move_id = self.battle.move["id"]      # read before answering: the battle forgets the move after the last answer
        out = self.battle.answer(given, self.elapsed)
        self.show_result(out, move_id)

    def time_up(self):
        """The timer ran out. The answer counts as wrong, just like a wrong answer."""
        move_id = self.battle.move["id"]
        out = self.battle.time_out()
        self.show_result(out, move_id, first_line=(t("time_up"), theme.BAD))

    def show_result(self, out, move_id, first_line=None):
        """Show right or wrong, the answer and the explanation, then the damage or the next question."""
        question = out["question"]
        lines = [first_line] if first_line else []
        lines.append((t("correct"), theme.GOOD) if out["correct"] else (t("wrong"), theme.BAD))
        sound.play("correct" if out["correct"] else "wrong")
        if out["correct"]:
            self.streak_popup(self.battle.engine.streak)
        if not out["correct"]:
            lines.append((t("the_answer", answer=answer_text(question)), theme.TEXT))
        if question.get("explanation"):
            lines.append((question["explanation"], theme.TEXT_DIM))
        if not out["done"]:
            self.show_message(lines, self.start_question)
            return
        lines.append((t("damage_dealt", damage=out["damage"]) if out["damage"] else t("miss"), theme.GOLD))
        self.pending_crit = out.get("crit", False)
        self.pending_weak = is_weak_hit(self.battle.results)
        if self.pending_crit:
            lines.append((t("crit_line"), theme.GOLD))       # explain WHY it hit harder: a fast answer
        if out["damage"]:
            # Start the attack animation. The hit itself lands a moment later (see land_hit).
            self.attack = ATTACK_SECONDS
            self.pending_damage = out["damage"]
            # The move's own look (arcs, orb, meteors...) plays with the same timing as the swing.
            self.skill = SkillLook(move_id, self.player_hand, self.enemy_center, ATTACK_SECONDS)
            sound.play(sound.skill_sound(self.skill.look["kind"]))     # swing, shoot or rain
        self.show_message(lines, self.victory if self.battle.won else self.enemy_turn)

    def attack_progress(self):
        """How far the player's attack has gone: 0.0 at its start, 1.0 when it is over."""
        return 1 - self.attack / ATTACK_SECONDS

    def streak_popup(self, streak):
        """ "3 in a row!" over the player after a right answer: bigger and brighter as the streak grows."""
        if streak < STREAK_POPUP_FROM:
            return
        fonts = self.game.fonts
        top = hud.streak_boxes()                       # the streak where the bonus stops growing
        font = fonts["title"] if streak >= top else fonts["big"]
        color = anim.blend(theme.GOLD, theme.GOLD_BRIGHT, min(1.0, streak / top))
        self.float_text(t("streak_popup", n=streak), color, STREAK_POPUP_AT, lift=60, font=font)

    def land_hit(self):
        """The moment the weapon, arrow or bolt reaches the enemy: shake, flash, sparks, damage number.

        The number shows how good the hit was: a crit is huge and bright, a weak hit small and grey."""
        fonts = self.game.fonts
        if self.pending_crit:
            font, color = fonts["title"], theme.GOLD_BRIGHT
        elif self.pending_weak:
            font, color = fonts["normal"], theme.TEXT_DIM
        else:
            font, color = fonts["big"], theme.GOLD
        self.float_text(f"-{self.pending_damage}", color, ENEMY_PANEL, font=font)
        self.pending_weak = False
        if self.pending_crit:
            self.float_text(t("crit_float"), theme.BAD, ENEMY_PANEL, lift=CRIT_LIFT)   # "CRIT!" under the number
            self.pending_crit = False
        self.pending_damage = 0
        sound.play("hit")
        strength = self.skill.look["shake"] if self.skill else 6     # stronger moves shake the screen harder
        self.shake.start(strength=strength, seconds=0.25)
        self.freeze = HIT_PAUSE
        self.flash = FLASH_SECONDS
        self.spark = SPARK_SECONDS

    def finish_attack(self):
        """The player pressed Enter before the attack was over: show its hit now and end it."""
        if self.pending_damage:
            self.land_hit()
            self.freeze = 0.0
        self.attack = 0.0
        if self.skill:
            self.skill.finish()

    def player_offset(self):
        """How far the player's picture is moved from its spot, as (x, y). The enemy is on the LEFT.

        This is what makes the standing picture look alive: it leans back and lunges for
        an attack, hops when using an item, and is knocked back when hurt.
        """
        if self.dying is not None:
            return 0, 0
        if self.attack > 0:
            lunge = LUNGE_PIXELS if (self.weapon is None or self.weapon.style == "melee") else 0
            progress = self.attack_progress()
            if progress < STRIKE_START:                          # wind up: lean back
                return round(WIND_UP_PIXELS * progress / STRIKE_START), 0
            if progress < IMPACT:                                # strike: forward
                forward = (progress - STRIKE_START) / (IMPACT - STRIKE_START)
                return round(WIND_UP_PIXELS - (WIND_UP_PIXELS + lunge) * forward), 0
            back = (progress - IMPACT) / (1 - IMPACT)            # recover: return to the spot
            return round(-lunge * (1 - back)), 0
        if self.using > 0:
            return 0, -round(HOP_PIXELS * math.sin(math.pi * (1 - self.using / USE_SECONDS)))
        if self.hurt > 0:
            return round(KNOCKBACK_PIXELS * self.hurt / HURT_SECONDS), 0
        return 0, 0

    def enemy_turn(self):
        out = self.battle.enemy_turn()
        if out.get("skipped"):   # after your miss, the enemy was caught off guard (effects.enemy_loses_turn)
            lines = [(t("enemy_loses_turn", enemy=self.enemy_name), theme.GOOD)]
        elif out["damage"] == 0:   # e.g. an effect cancelled the attack
            lines = [(t("enemy_misses", enemy=self.enemy_name), theme.GOOD)]
        else:
            lines = [(t("enemy_hits", enemy=self.enemy_name, damage=out["damage"]), theme.BAD)]
            self.hurt = HURT_SECONDS
            sound.play("hurt")
            self.shake.start(strength=10, seconds=0.3)
            self.red_flash = RED_FLASH_SECONDS
            self.float_text(f"-{out['damage']}", theme.BAD, PLAYER_ART)
        taunt = self.show_taunt(out)
        if taunt:
            lines.append((taunt, theme.GOLD))
        self.show_message(lines, self.defeat if self.battle.lost else self.back_to_choose)

    def show_taunt(self, out):
        """If the enemy changed (out["taunt"] is a strings key), show its bubble over the enemy.
        Returns the long text for the message box (it also says what changed), or None."""
        if not out.get("taunt"):
            return None
        values = out.get("taunt_values", {})
        names = {"enemy": self.enemy_name, "topic": topic_name(values["topic"]) if "topic" in values else ""}
        short = t(f"{out['taunt']}_bubble", **names)
        self.taunt_bubble = widgets.speech_bubble(self.game.fonts["small"], short, TAUNT_BUBBLE_WIDTH)
        self.taunt_time = TAUNT_SECONDS
        sound.play("taunt")
        return t(out["taunt"], **names)

    def show_learning(self):
        """Work out the "what you learned" bars once, for the message at the end of the fight."""
        self.learning = learning_panel.learning_rows(self.learned_before, self.game.run_state.tracker)
        self.learning_shown_at = anim.now()

    def victory(self):
        self.show_learning()
        sound.play("victory")
        self.show_message([(t("victory_fight", enemy=self.enemy_name), theme.GOOD)],
                          lambda: self.finish(won=True))

    def defeat(self):
        self.show_learning()
        self.dying = 0.0
        sound.play("defeat")
        self.show_message([(t("defeat_fight", enemy=self.enemy_name), theme.BAD)],
                          lambda: self.finish(won=False))

    # --- input -------------------------------------------------------------
    def handle_event(self, event):
        if self.state == "choose":
            self.input_choose(event)
        elif self.state == "items":
            self.input_items(event)
        elif self.state == "question":
            self.input_question(event)
        elif event.type == pygame.KEYDOWN and event.key in ENTER_KEYS + (pygame.K_SPACE,):
            self.finish_attack()
            self.next_step()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.finish_attack()
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
            elif event.key == pygame.K_i:
                self.open_items()
            elif event.key == pygame.K_ESCAPE and not self.enemy.boss:
                sound.play("flee")
                self.finish(won=False, fled=True)
        elif event.type == pygame.MOUSEMOTION:
            hovered = self.hotbar.index_at(event.pos)
            if hovered is not None:
                self.selected = hovered   # pointing at a slot shows its details in the panel
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self.hotbar.index_at(event.pos)
            if clicked is not None:
                self.pick_move(clicked)
            elif self.items_button.hit(event.pos):
                self.open_items()

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
        if self.freeze > 0:
            self.freeze -= dt       # hit pause: nothing moves for a few frames
            return
        self.flash = max(0.0, self.flash - dt)
        self.red_flash = max(0.0, self.red_flash - dt)
        self.taunt_time = max(0.0, self.taunt_time - dt)
        self.input.update(dt)
        self.enemy_actor.update(dt)
        self.player_actor.update(dt)
        self.hurt = max(0.0, self.hurt - dt)
        self.attack = max(0.0, self.attack - dt)
        self.spark = max(0.0, self.spark - dt)
        if self.pending_damage and self.attack_progress() >= IMPACT:
            self.land_hit()
        self.using = max(0.0, self.using - dt)
        if self.skill:
            self.skill.update(dt)
            if not self.skill.alive():
                self.skill = None
        if self.dying is not None:
            self.dying += dt
        self.floating = [text for text in self.floating if text.alive()]
        if self.state == "question":
            self.elapsed += dt
            if self.battle.time_is_up(self.elapsed):
                self.time_up()

    def draw(self, surface):
        offset = self.shake.offset()
        if offset == (0, 0):
            self.draw_scene(surface)
            return
        # Shaking: draw the whole screen onto a spare picture, then put that on the real
        # screen a few pixels off. The spare picture is made once, not every frame.
        self.buffer.fill(theme.BACKGROUND)
        self.draw_scene(self.buffer)
        surface.fill(theme.BACKGROUND)
        surface.blit(self.buffer, offset)

    def draw_scene(self, surface):
        fonts = self.game.fonts
        hud.draw_player_panel(surface, fonts, self.player)
        self.draw_enemy(surface, fonts)
        self.draw_player(surface)
        theme.draw_frame(surface, CONTENT)
        if self.state == "choose":
            self.draw_choose(surface, fonts)
            self.items_button.draw(surface, fonts["small"], pygame.mouse.get_pos())
        elif self.state == "items":
            self.draw_items(surface, fonts)
        elif self.state == "question":
            self.draw_question(surface, fonts)
        else:
            self.draw_message(surface, fonts)
        # The streak sits under the status panel: how many right answers in a row, and what it adds.
        hud.draw_streak(surface, fonts, self.battle.engine.streak, (hud.PLAYER_PANEL.x + 4, hud.PLAYER_PANEL.bottom + 12))
        choosing = self.state == "choose"
        self.hotbar.draw(surface, fonts, pygame.mouse.get_pos(),
                         selected=self.selected if choosing else None, active=choosing)
        if self.skill:
            self.skill.draw(surface)
        for text in self.floating:
            text.draw(surface)
        if self.red_flash > 0:
            # Strong at first, then fading: the whole screen goes a little red for a moment.
            self.red_layer.set_alpha(round(RED_FLASH_ALPHA * self.red_flash / RED_FLASH_SECONDS))
            surface.blit(self.red_layer, (0, 0))

    def draw_enemy(self, surface, fonts):
        inside = theme.draw_frame(surface, ENEMY_PANEL)
        enemy = self.enemy
        name = f"{self.enemy_name}  ({t('boss_tag')})" if enemy.boss else self.enemy_name
        widgets.text(surface, fonts["normal"], name, theme.GOLD, (inside.centerx, inside.y), "midtop")
        widgets.bar(surface, (inside.x, inside.y + 30, inside.width, 22), enemy.hp, enemy.max_hp,
                    theme.HP, theme.HP_BACK, t("hp_label", hp=enemy.hp, max_hp=enemy.max_hp), fonts["small"],
                    trail=self.enemy_trail.follow(enemy.hp))
        image = self.enemy_actor.image()
        rect = image.get_rect(midbottom=(inside.centerx, inside.bottom))
        surface.blit(self.white_copy(image) if self.flash > 0 else image, rect)
        self.enemy_center = rect.center
        if self.spark > 0 and self.sparks:
            # Hit sparks over the enemy right after the player's attack landed.
            progress = 1 - self.spark / SPARK_SECONDS
            spark = self.sparks[min(int(progress * len(self.sparks)), len(self.sparks) - 1)]
            surface.blit(spark, spark.get_rect(center=rect.center))
        if self.taunt_time > 0 and self.taunt_bubble:
            # The bubble sits in the empty part left of the enemy, under the HP bar, so it never
            # covers the enemy itself.
            bubble = self.taunt_bubble.get_rect(topleft=(inside.x + 4, inside.y + 60))
            bubble.right = min(bubble.right, rect.left + image.get_bounding_rect().left - 4)
            surface.blit(self.taunt_bubble, bubble)

    def player_image(self):
        """Which picture of the player to show: dying, attacking, using an item, hurt, or just standing."""
        actor = self.player_actor
        if self.dying is not None:
            return actor.image_at("die", self.dying / DIE_SECONDS)
        if self.attack > 0:
            return actor.image_at("attack", self.attack_progress())   # own attack pictures if the art has them
        if self.using > 0:
            return actor.image_at("use", 1 - self.using / USE_SECONDS)
        return actor.image("hit" if self.hurt > 0 else None)

    def white_copy(self, image):
        """The same picture with every pixel white: the enemy flashes like this when it is hit."""
        if id(image) not in self.white:
            mask = pygame.mask.from_surface(image)
            self.white[id(image)] = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        return self.white[id(image)]

    def draw_player(self, surface):
        """The player's picture in its own small panel; it shows the "hit" frame right after being hurt."""
        inside = theme.draw_frame(surface, PLAYER_ART)
        image = self.player_image()
        offset_x, offset_y = self.player_offset()
        feet = (inside.centerx + 16 + offset_x, inside.bottom + offset_y)
        rect = image.get_rect(midbottom=feet)
        surface.blit(image, rect)
        self.player_center = rect.center
        self.player_hand = rect.midleft          # used when no weapon is drawn
        if self.weapon and self.dying is None:
            swing = self.attack_progress() if self.attack > 0 else None
            self.weapon.draw(surface, feet, facing_left=True, swing=swing)
            hand = self.weapon.hand(*feet, facing_left=True)
            self.player_hand = hand
            # A skill that flies or falls brings its own picture; then the weapon's arrow or bolt is not drawn too.
            if not (self.skill and self.skill.kind in ("projectile", "rain")):
                self.weapon.draw_projectile(surface, hand, self.enemy_center, True, swing)

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
        # The timer counts down. It shows the time left, rounded up, so it reads 1 s until the very last moment.
        left = max(0, self.battle.time_limit - self.elapsed)
        widgets.text(surface, small, t("seconds", s=math.ceil(left)), theme.TEXT_DIM, INSIDE.topright, "topright")

        y = INSIDE.y + 30
        for line in self.question_lines:
            widgets.text(surface, self.question_font, line, theme.TEXT, (INSIDE.x, y))
            y += self.question_font.get_height() + 6

        if question["type"] == "typed":
            self.input.draw(surface, fonts["question"])
            self.hint(surface, fonts, t("hint_typed"))
            return
        multi = question["type"] == "multi_select"
        mouse = pygame.mouse.get_pos()
        for i, button in enumerate(self.choice_buttons):
            ticked = multi and i in self.ticked
            mark = ("[x] " if ticked else "[  ] ") if multi else ""
            button.label = f"{i + 1}. {mark}{question['choices'][i]}"
            button.draw(surface, fonts["answer"], mouse, selected=ticked)
        count = len(self.choice_buttons)
        self.hint(surface, fonts, t("hint_multi", n=count) if multi else t("hint_choice", n=count))

    def draw_message(self, surface, fonts):
        y = INSIDE.y + 6
        for i, (line, color) in enumerate(self.lines):
            font = fonts["big"] if i == 0 else fonts["normal"]
            y = widgets.wrapped(surface, font, line, color, (INSIDE.x, y), INSIDE.width) + 8
        # Only set when the fight is over (victory or defeat): what this fight taught you.
        learning_panel.draw_learning(surface, fonts, self.learning, (INSIDE.x, y + 12), self.learning_shown_at)
        self.hint(surface, fonts, t("press_continue"))
