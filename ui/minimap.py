"""The small map in the corner: only the cells the player has seen (owner: B)."""
import pygame

from dungeon.floor import STAIRS, WALL
from ui import theme

CELL = 4                       # pixels per floor cell on the minimap
FLOOR_COLOR = (112, 100, 88)
STAIRS_COLOR = theme.GOLD
CHEST_COLOR = (214, 140, 50)
ENEMY_COLOR = theme.BAD
GUARD_COLOR = (220, 90, 200)   # bosses and mini-bosses
PLAYER_COLOR = (120, 220, 240)


class Minimap:
    def __init__(self, floor, topright):
        self.floor = floor
        self.rect = pygame.Rect(0, 0, floor.width * CELL + 16, floor.height * CELL + 16)
        self.rect.topright = topright
        # The seen floor cells are painted onto this picture once, when they are first seen.
        self.picture = pygame.Surface((floor.width * CELL, floor.height * CELL), pygame.SRCALPHA)

    def reveal(self, cells):
        """Paint newly seen cells. Walls are left dark, so rooms and corridors stand out."""
        for x, y in cells:
            cell = self.floor.grid[y][x]
            if cell != WALL:
                color = STAIRS_COLOR if cell == STAIRS else FLOOR_COLOR
                self.picture.fill(color, (x * CELL, y * CELL, CELL, CELL))

    def dot(self, surface, pos, color, size=CELL):
        x = self.rect.x + 8 + pos[0] * CELL - (size - CELL) // 2
        y = self.rect.y + 8 + pos[1] * CELL - (size - CELL) // 2
        surface.fill(color, (x, y, size, size))

    def draw(self, surface, seen, player_pos):
        """seen: the set of cells the player has seen. Only things on seen cells are shown."""
        pygame.draw.rect(surface, theme.OUTLINE, self.rect)
        pygame.draw.rect(surface, theme.METAL_DARK, self.rect.inflate(-4, -4))
        pygame.draw.rect(surface, theme.PANEL_FILL, self.rect.inflate(-8, -8))
        surface.blit(self.picture, (self.rect.x + 8, self.rect.y + 8))
        for chest in self.floor.chests:
            if chest["pos"] in seen and not chest["opened"]:
                self.dot(surface, chest["pos"], CHEST_COLOR)
        for enemy in self.floor.enemies:
            if enemy["pos"] in seen:
                self.dot(surface, enemy["pos"], GUARD_COLOR if enemy["guard"] else ENEMY_COLOR)
        self.dot(surface, player_pos, PLAYER_COLOR, size=CELL + 2)
