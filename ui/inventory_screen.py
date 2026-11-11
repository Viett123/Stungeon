"""The bag: look at items, use potions, put equipment on and take it off (owner: B).

The rules are in systems/inventory.py. This file only draws and reads input.
The selection is one number: 0 .. size-1 are the bag slots, the numbers after that
are the equipment slots (weapon, head, body, legs, shoes, two accessories).
"""
import pygame

from core.scene import Scene
from core.strings import t
from systems import inventory, items
from ui import slots, theme, widgets
from ui.item_info import item_icon, item_lines

COLUMNS = 5
GAP = 8
PANEL = pygame.Rect(170, 60, 940, 600)
EQUIP_COLUMNS = 4          # equipment slots per row
EQUIP_STEP_X = 112
EQUIP_STEP_Y = 100
ENTER_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)
TAKE_OFF_KEYS = (pygame.K_x, pygame.K_BACKSPACE, pygame.K_DELETE)


class InventoryScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.under = game.scenes.current      # the dungeon, shown darkened behind the bag
        self.player = game.run_state.player
        self.size = items.inventory_size()
        self.selected = 0
        self.message = ""
        inside = theme.inner(PANEL)
        step = slots.SLOT + GAP
        self.bag_rects = [pygame.Rect(inside.x + (i % COLUMNS) * step, inside.y + 60 + (i // COLUMNS) * step,
                                      slots.SLOT, slots.SLOT) for i in range(self.size)]
        self.side_x = inside.x + COLUMNS * step + 36      # where the right-hand column starts
        self.equip_rects = [pygame.Rect(self.side_x + (i % EQUIP_COLUMNS) * EQUIP_STEP_X,
                                        inside.y + 84 + (i // EQUIP_COLUMNS) * EQUIP_STEP_Y, slots.SLOT, slots.SLOT)
                            for i in range(len(inventory.EQUIP_SLOTS))]
        self.refresh()

    def refresh(self):
        """Read the bag again. Called after every change, so draw() never reads data files."""
        font = self.game.fonts["small"]
        self.bag = [items.get_item(item_id) for item_id in self.player.inventory]
        self.worn = [items.get_item(self.player.equipped[slot]) if slot in self.player.equipped else None
                     for slot in inventory.EQUIP_SLOTS]
        self.icons = {item["id"]: item_icon(item, font) for item in self.bag + [w for w in self.worn if w]}

    def on_equipment(self):
        """True if the selection is on an equipment slot (not in the bag)."""
        return self.selected >= self.size

    def selected_item(self):
        if self.on_equipment():
            return self.worn[self.selected - self.size]
        return self.bag[self.selected] if self.selected < len(self.bag) else None

    # --- actions -------------------------------------------------------------
    def act(self):
        """Enter or a second click: use, equip or take off the selected item."""
        item = self.selected_item()
        if item is None:
            return
        if self.on_equipment():
            self.take_off()
        elif item["kind"] == "consumable":
            done = inventory.use_item(self.player, item["id"])
            self.message = t("inv_used", item=item["name"]) if done else t("inv_no_effect", item=item["name"])
        else:
            inventory.equip(self.player, item["id"])
            self.message = t("inv_equipped", item=item["name"])
        self.refresh()

    def take_off(self):
        """Move the selected equipment back into the bag."""
        item = self.selected_item()
        if item is None or not self.on_equipment():
            return
        slot = inventory.EQUIP_SLOTS[self.selected - self.size]
        done = inventory.unequip(self.player, slot)
        self.message = t("inv_unequipped", item=item["name"]) if done else t("inv_bag_full")
        self.refresh()

    def switch_side(self):
        """Tab jumps between the bag and the equipment slots."""
        self.selected = 0 if self.on_equipment() else self.size

    def handle_event(self, event):
        total = self.size + len(inventory.EQUIP_SLOTS)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_i):
                self.game.scenes.pop()
            elif event.key in ENTER_KEYS:
                self.act()
            elif event.key in TAKE_OFF_KEYS:
                self.take_off()
            elif event.key == pygame.K_TAB:
                self.switch_side()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % total
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % total
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.move_rows(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.move_rows(1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.bag_rects + self.equip_rects):
                if rect.collidepoint(event.pos):
                    if i == self.selected:
                        self.act()       # clicking the selected slot again uses it
                    self.selected = i

    def move_rows(self, rows):
        """Up or down inside the bag grid, or inside the equipment grid."""
        if self.on_equipment():
            target = self.selected + rows * EQUIP_COLUMNS
            if self.size <= target < self.size + len(inventory.EQUIP_SLOTS):
                self.selected = target
        else:
            target = self.selected + rows * COLUMNS
            if 0 <= target < self.size:
                self.selected = target

    # --- drawing -------------------------------------------------------------
    def draw(self, surface):
        self.under.draw(surface)
        widgets.dim(surface)
        fonts = self.game.fonts
        small = fonts["small"]
        inside = theme.draw_frame(surface, PANEL)
        widgets.text(surface, fonts["big"], t("inv_title"), theme.GOLD, inside.topleft)
        widgets.text(surface, small, t("inv_count", n=len(self.bag), size=self.size), theme.TEXT_DIM,
                     (self.bag_rects[COLUMNS - 1].right, inside.y + 14), "topright")
        widgets.text(surface, fonts["normal"], t("inv_equipment"), theme.GOLD, (self.side_x, inside.y + 8))

        for i, rect in enumerate(self.bag_rects):
            item = self.bag[i] if i < len(self.bag) else None
            slots.draw_slot(surface, rect, self.icons[item["id"]] if item else None, highlighted=(i == self.selected))
        for i, (rect, slot, item) in enumerate(zip(self.equip_rects, inventory.EQUIP_SLOTS, self.worn)):
            widgets.text(surface, small, t(f"slot_{slot}"), theme.TEXT_DIM, (rect.x, rect.y - 24))
            slots.draw_slot(surface, rect, self.icons[item["id"]] if item else None,
                            highlighted=(self.size + i == self.selected))

        self.draw_details(surface, fonts, inside)
        if self.message:
            widgets.text(surface, small, self.message, theme.GOLD, (inside.x, inside.bottom - 28), "bottomleft")
        widgets.text(surface, small, t("inv_hint"), theme.TEXT_DIM, inside.bottomleft, "bottomleft")

    def draw_details(self, surface, fonts, inside):
        """Name, rarity, kind and description of the selected item, under the equipment slots."""
        item = self.selected_item()
        x = self.side_x
        y = self.equip_rects[-1].bottom + 26
        width = inside.right - x
        if item is None:
            widgets.text(surface, fonts["small"], t("inv_empty_slot"), theme.TEXT_DIM, (x, y))
            return
        (name, name_color), (kind, kind_color), (text, text_color) = item_lines(item)
        widgets.text(surface, fonts["normal"], name, name_color, (x, y))
        widgets.text(surface, fonts["small"], kind, kind_color, (x, y + 30))
        y = widgets.wrapped(surface, fonts["small"], text, text_color, (x, y + 62), width)
        if self.on_equipment():
            action = t("inv_action_unequip")
        else:
            action = t("inv_action_use") if item["kind"] == "consumable" else t("inv_action_equip")
        widgets.text(surface, fonts["small"], action, theme.GOLD, (x, y + 8))
