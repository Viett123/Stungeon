"""The dungeon you walk through (owner: A). PLACEHOLDER: one room, move a square around."""
import pygame

from core import settings
from core.game import draw_text
from core.scene import Scene
from core.strings import t
from dungeon.floor import STAIRS, WALL, generate_floor

MOVE_KEYS = {
    pygame.K_UP: (0, -1), pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0),
}
TOP = 48   # leave one tile row at the top for the status line


class DungeonScene(Scene):
    def __init__(self, game, floor_number):
        super().__init__(game)
        self.floor = generate_floor(floor_number, seed=floor_number)
        self.player_pos = self.floor.start

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.go_to_title()
        elif event.key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[event.key]
            x, y = self.player_pos[0] + dx, self.player_pos[1] + dy
            if self.floor.is_walkable(x, y):
                self.player_pos = (x, y)

    def draw(self, surface):
        tile = settings.TILE
        for y, row in enumerate(self.floor.grid):
            for x, cell in enumerate(row):
                color = {WALL: settings.COLOR_WALL, STAIRS: settings.COLOR_STAIRS}.get(cell, settings.COLOR_FLOOR)
                pygame.draw.rect(surface, color, (x * tile, TOP + y * tile, tile - 1, tile - 1))
        px, py = self.player_pos
        pygame.draw.rect(surface, settings.COLOR_PLAYER, (px * tile + 8, TOP + py * tile + 8, tile - 16, tile - 16))

        f = self.game.fonts["normal"]
        draw_text(surface, f, t("floor_label", n=self.floor.number), settings.COLOR_TEXT, (80, 24))
        status = t("on_stairs") if self.player_pos == self.floor.stairs else t("dungeon_hint")
        draw_text(surface, f, status, settings.COLOR_DIM, (settings.SCREEN_W // 2, 24))
