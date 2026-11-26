"""The shop (owner: B): between two floors, or a wandering merchant met in a room.

The rules and prices are in systems/shop.py and data/shop.json. This file only draws
and reads input. Tab (or Left/Right) switches between buying and selling.

Two kinds of shop:
  ShopScene(game)                  - after a floor. Leaving goes on to the next floor (core/flow.py).
  ShopScene(game, wandering=True)  - a merchant in a dungeon room. Leaving goes back to the dungeon.
"""
import pygame

from core import flow, sound
from core.scene import Scene
from core.strings import t
from systems import items, shop
from ui import theme, widgets
from ui.button import Button
from ui.item_info import item_icon, item_lines
from ui.merchant import Merchant

PANEL = pygame.Rect(190, 70, 900, 580)
ROW_H, GAP = 52, 8
LIST_TOP = 92             # how far below the top of the panel the list starts (the tabs are above it)
TABS_TOP = 54             # where the Buy / Sell tabs are, under the title
VISIBLE_ROWS = 7          # rows shown at once; a longer list scrolls with the selection
MERCHANT_SCALE = 6        # the shopkeeper is drawn 6 times the size of the art
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)
SWITCH_KEYS = (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d)
MODES = ["buy", "sell"]


class ShopScene(Scene):
    def __init__(self, game, wandering=False):
        super().__init__(game)
        self.run = game.run_state
        self.player = self.run.player
        self.wandering = wandering
        self.under = game.scenes.current if wandering else None     # the dungeon, shown darkened behind
        self.mode = "buy"
        self.selected = 0
        self.top = 0              # the first row shown (for scrolling)
        self.message = ""
        self.inside = theme.inner(PANEL)
        # The stock does not change while the shop is open, so read it once.
        ids = shop.wandering_stock(self.run.floor_number) if wandering else shop.stock(self.run.floor_number)
        self.stock = [items.get_item(item_id) for item_id in ids]
        self.rows = [Button((self.inside.x, self.inside.y + LIST_TOP + i * (ROW_H + GAP), 520, ROW_H), "")
                     for i in range(VISIBLE_ROWS)]
        label = t("shop_leave_wandering") if wandering else t("shop_leave", n=self.run.floor_number + 1)
        self.leave = Button((self.inside.right - 330, self.inside.bottom - 84, 330, 48), label)
        self.side_x = self.inside.x + 560
        self.merchant = Merchant(MERCHANT_SCALE)
        self.refresh()

    # --- the list on the left ---------------------------------------------------
    def refresh(self):
        """Work out the list for the current mode. Called after every sale, so draw() reads no files."""
        font = self.game.fonts["small"]
        if self.mode == "buy":
            self.entries = [(item, None) for item in self.stock]
        else:
            # The bag, each kind of item once, with how many there are. Worn equipment is not sold:
            # take it off in the bag first (so nobody sells their weapon by accident).
            ids = []
            for item_id in self.player.inventory:
                if item_id not in ids:
                    ids.append(item_id)
            self.entries = [(items.get_item(i), self.player.inventory.count(i)) for i in ids]
        self.icons = [item_icon(item, font) for item, _ in self.entries]
        self.selected = min(self.selected, max(0, len(self.entries) - 1))
        self.scroll()

    def scroll(self):
        """Move the shown part of the list so the selected row is always visible."""
        if self.selected < self.top:
            self.top = self.selected
        elif self.selected >= self.top + VISIBLE_ROWS:
            self.top = self.selected - VISIBLE_ROWS + 1

    def price(self, item):
        return shop.buy_price(item) if self.mode == "buy" else shop.sell_price(item)

    def switch_mode(self):
        self.mode = MODES[(MODES.index(self.mode) + 1) % len(MODES)]
        self.selected = self.top = 0
        self.message = ""
        self.refresh()

    # --- actions -----------------------------------------------------------------
    def act(self):
        """Enter: buy or sell the selected item."""
        if not self.entries:
            return
        item, _ = self.entries[self.selected]
        if self.mode == "buy":
            result = shop.buy(self.player, item["id"])
            self.message = t(f"shop_{result}", item=item["name"])
            done = result == "ok"
        else:
            done = shop.sell(self.player, item["id"])
            self.message = t("shop_sold", item=item["name"], price=shop.sell_price(item))
        sound.play("buy" if done else "wrong")
        if done:
            self.merchant.react()          # he hops with joy
        self.refresh()

    def go(self):
        """Leave the shop: back to the dungeon (wandering merchant) or on to the next floor."""
        if self.wandering:
            self.game.scenes.pop()
        else:
            flow.offer_choice(self.game)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            count = max(1, len(self.entries))
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % count
                self.scroll()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % count
                self.scroll()
            elif event.key in SWITCH_KEYS:
                self.switch_mode()
            elif event.key in ENTER_KEYS:
                self.act()
            elif event.key in (pygame.K_c, pygame.K_ESCAPE):
                self.go()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.leave.hit(event.pos):
                self.go()
                return
            for i, row in enumerate(self.rows):
                index = self.top + i
                if row.hit(event.pos) and index < len(self.entries):
                    if index == self.selected:
                        self.act()   # clicking the selected row again buys or sells it
                    self.selected = index

    # --- drawing -----------------------------------------------------------------
    def draw(self, surface):
        if self.under:
            self.under.draw(surface)
            widgets.dim(surface)
        fonts = self.game.fonts
        small = fonts["small"]
        inside = self.inside
        mouse = pygame.mouse.get_pos()
        theme.draw_frame(surface, PANEL)
        title = t("shop_title_wandering") if self.wandering else t("shop_title")
        widgets.text(surface, fonts["big"], title, theme.GOLD, inside.topleft)
        widgets.text(surface, fonts["normal"], t("shop_gold", gold=self.player.gold), theme.GOLD,
                     inside.topright, "topright")
        self.draw_tabs(surface, fonts)
        self.draw_list(surface, fonts, mouse)
        self.draw_details(surface, fonts)
        self.merchant.draw(surface, (inside.right - 70, self.leave.rect.top - 14))
        self.leave.draw(surface, fonts["normal"], mouse)
        if self.message:
            widgets.text(surface, small, self.message, theme.GOLD, (inside.x, inside.bottom - 28), "bottomleft")
        widgets.text(surface, small, t("shop_hint_wandering") if self.wandering else t("shop_hint"),
                     theme.TEXT_DIM, inside.bottomleft, "bottomleft")

    def draw_tabs(self, surface, fonts):
        """'Buy' and 'Sell' under the title: the open one is gold and underlined, the other one dim."""
        x = self.inside.x
        for mode in MODES:
            open_ = mode == self.mode
            color = theme.GOLD if open_ else theme.TEXT_DIM
            rect = widgets.text(surface, fonts["normal"], t(f"shop_tab_{mode}"), color, (x, self.inside.y + TABS_TOP))
            if open_:
                pygame.draw.line(surface, color, (rect.left, rect.bottom + 2), (rect.right, rect.bottom + 2), 2)
            x = rect.right + 30

    def draw_list(self, surface, fonts, mouse):
        if not self.entries:
            key = "shop_nothing_to_sell" if self.mode == "sell" else "shop_nothing_to_buy"
            widgets.text(surface, fonts["normal"], t(key), theme.TEXT_DIM, self.rows[0].rect.midleft)
            return
        shown = self.entries[self.top: self.top + VISIBLE_ROWS]
        for i, (row, (item, count)) in enumerate(zip(self.rows, shown)):
            index = self.top + i
            row.label = ""
            row.draw(surface, fonts["normal"], mouse, selected=(index == self.selected))
            icon = self.icons[index]
            surface.blit(icon, icon.get_rect(center=(row.rect.x + 32, row.rect.centery)))   # narrow icons stay centred
            name = item["name"] if count is None else t("item_line", name=item["name"], n=count)
            widgets.text(surface, fonts["normal"], name, theme.TEXT, (row.rect.x + 70, row.rect.centery), "midleft")
            affordable = self.mode == "sell" or self.player.gold >= self.price(item)
            widgets.text(surface, fonts["normal"], t("shop_price", price=self.price(item)),
                         theme.GOLD if affordable else theme.BAD, (row.rect.right - 14, row.rect.centery), "midright")
        # Small arrows beside the list when there are more rows above or below.
        x = self.rows[0].rect.right + 16
        if self.top > 0:
            y = self.rows[0].rect.y + 4
            pygame.draw.polygon(surface, theme.TEXT_DIM, [(x, y + 10), (x + 12, y + 10), (x + 6, y)])
        if self.top + VISIBLE_ROWS < len(self.entries):
            y = self.rows[-1].rect.bottom - 14
            pygame.draw.polygon(surface, theme.TEXT_DIM, [(x, y), (x + 12, y), (x + 6, y + 10)])

    def draw_details(self, surface, fonts):
        if not self.entries:
            return
        item, _ = self.entries[self.selected]
        (name, name_color), (kind, kind_color), (text, text_color) = item_lines(item)
        widgets.text(surface, fonts["normal"], name, name_color, (self.side_x, self.inside.y + 74))
        widgets.text(surface, fonts["small"], kind, kind_color, (self.side_x, self.inside.y + 104))
        widgets.wrapped(surface, fonts["small"], text, text_color, (self.side_x, self.inside.y + 138),
                        self.inside.right - self.side_x)
