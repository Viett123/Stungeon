"""The shop between two floors (owner: B).

The rules and prices are in systems/shop.py and data/shop.json. This file only draws
and reads input. You can buy here; selling exists in systems/shop.py but has no screen yet.
"""
import pygame

from core import flow
from core.scene import Scene
from core.strings import t
from systems import items, shop
from ui import theme, widgets
from ui.button import Button
from ui.item_info import item_icon, item_lines

PANEL = pygame.Rect(190, 70, 900, 580)
ROW_H, GAP = 52, 8
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


class ShopScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.run = game.run_state
        self.player = self.run.player
        self.selected = 0
        self.message = ""
        inside = theme.inner(PANEL)
        font = game.fonts["small"]
        # The stock does not change while the shop is open, so read it once.
        self.stock = [items.get_item(item_id) for item_id in shop.stock(self.run.floor_number)]
        self.icons = [item_icon(item, font) for item in self.stock]
        self.rows = [Button((inside.x, inside.y + 70 + i * (ROW_H + GAP), 520, ROW_H), "")
                     for i in range(len(self.stock))]
        self.leave = Button((inside.right - 330, inside.bottom - 84, 330, 48),
                            t("shop_leave", n=self.run.floor_number + 1))
        self.side_x = inside.x + 560

    def buy_selected(self):
        item = self.stock[self.selected]
        result = shop.buy(self.player, item["id"])
        self.message = t(f"shop_{result}", item=item["name"])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.stock)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.stock)
            elif event.key in ENTER_KEYS:
                self.buy_selected()
            elif event.key in (pygame.K_c, pygame.K_ESCAPE):
                flow.offer_choice(self.game)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.leave.hit(event.pos):
                flow.offer_choice(self.game)
                return
            for i, row in enumerate(self.rows):
                if row.hit(event.pos):
                    if i == self.selected:
                        self.buy_selected()   # clicking the selected row again buys it
                    self.selected = i

    def draw(self, surface):
        fonts = self.game.fonts
        small = fonts["small"]
        mouse = pygame.mouse.get_pos()
        inside = theme.draw_frame(surface, PANEL)
        widgets.text(surface, fonts["big"], t("shop_title"), theme.GOLD, inside.topleft)
        widgets.text(surface, fonts["normal"], t("shop_gold", gold=self.player.gold), theme.GOLD,
                     inside.topright, "topright")

        for i, (row, item, icon) in enumerate(zip(self.rows, self.stock, self.icons)):
            affordable = self.player.gold >= shop.buy_price(item)
            row.label = ""
            row.draw(surface, fonts["normal"], mouse, selected=(i == self.selected))
            surface.blit(icon, icon.get_rect(center=(row.rect.x + 32, row.rect.centery)))   # narrow icons stay centred
            widgets.text(surface, fonts["normal"], item["name"], theme.TEXT, (row.rect.x + 70, row.rect.centery), "midleft")
            widgets.text(surface, fonts["normal"], t("shop_price", price=shop.buy_price(item)),
                         theme.GOLD if affordable else theme.BAD, (row.rect.right - 14, row.rect.centery), "midright")

        item = self.stock[self.selected]
        (name, name_color), (kind, kind_color), (text, text_color) = item_lines(item)
        widgets.text(surface, fonts["normal"], name, name_color, (self.side_x, inside.y + 74))
        widgets.text(surface, small, kind, kind_color, (self.side_x, inside.y + 104))
        widgets.wrapped(surface, small, text, text_color, (self.side_x, inside.y + 138), inside.right - self.side_x)

        self.leave.draw(surface, fonts["normal"], mouse)
        if self.message:
            widgets.text(surface, small, self.message, theme.GOLD, (inside.x, inside.bottom - 28), "bottomleft")
        widgets.text(surface, small, t("shop_hint"), theme.TEXT_DIM, inside.bottomleft, "bottomleft")
