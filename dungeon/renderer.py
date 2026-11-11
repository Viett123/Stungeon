"""Draws a floor and the things on it (owner: A).

The floor never changes while you walk on it, so it is drawn ONCE when the floor
starts, onto two big images:
  map_image  - floors, brick walls and wall side lines
  cap_image  - the stone strips on top of walls. They are drawn AFTER the characters,
               so someone standing behind a wall is partly hidden by it.
Every frame we only copy the visible part of those images to the screen.
"""
import pygame

from core import settings
from dungeon import sprites, tiles

TILE = settings.TILE
FLOOR_VARIANTS = 32           # 1 tile in 32 gets each special floor picture (tile_floor_0.png, ...)
WALL_VARIANTS = 20            # 1 brick in 20 gets each special wall picture (tile_wall_front_0.png, ...)
SHADOW_HEIGHT = 12            # pixels of shadow a wall casts on the floor below it
SHADOW_COLOR = (0, 0, 0, 70)  # black, mostly see-through


def _variant(x, y, count):
    """A number from 0 to count-1 that looks random but is always the same for the same cell."""
    return (x * 73 + y * 151 + x * y * 7) % count


class DungeonRenderer:
    def __init__(self, floor, folder="", background=sprites.VOID):
        """folder and background come from the floor's theme (data/themes.json)."""
        self.floor = floor
        self.folder = folder
        self.background = tuple(background)
        self.world_w = floor.width * TILE
        self.world_h = floor.height * TILE
        self.map_image = self._draw_map()
        self.cap_image = self._draw_caps()

    # --- once per floor ----------------------------------------------------
    def _draw_map(self):
        image = pygame.Surface((self.world_w, self.world_h))
        image.fill(self.background)
        shadow = pygame.Surface((TILE, SHADOW_HEIGHT), pygame.SRCALPHA)
        shadow.fill(SHADOW_COLOR)
        grid = self.floor.grid
        for y in range(self.floor.height):
            for x in range(self.floor.width):
                for name in tiles.base_tiles(grid, x, y):
                    image.blit(self._tile_image(name, x, y), (x * TILE, y * TILE))
                if tiles.in_wall_shadow(grid, x, y):
                    image.blit(shadow, (x * TILE, y * TILE))
        return image

    def _tile_image(self, name, x, y):
        if name == tiles.FLOOR:
            return sprites.tile_sprite(name, _variant(x, y, FLOOR_VARIANTS), self.folder)
        if name == tiles.BRICK:
            return sprites.tile_sprite(name, _variant(x, y, WALL_VARIANTS), self.folder)
        return sprites.tile_sprite(name, folder=self.folder)

    def _draw_caps(self):
        image = pygame.Surface((self.world_w, self.world_h), pygame.SRCALPHA)   # see-through
        cap = sprites.tile_sprite(tiles.CAP, folder=self.folder)
        for y in range(self.floor.height):
            for x in range(self.floor.width):
                if tiles.has_cap(self.floor.grid, x, y):
                    image.blit(cap, (x * TILE, y * TILE))
        return image

    # --- every frame -------------------------------------------------------
    def draw(self, surface, view, camera, things):
        """Draw the visible part of the floor into the rectangle `view` on `surface`.

        things: list of (feet_x, feet_y, image) in world pixels: characters and chests.
        The image stands with its bottom middle on that point, so a tall image
        overlaps the tile above it. A fourth value, lift, draws the image that many
        pixels higher without changing its place in the drawing order (a held weapon).
        """
        surface.set_clip(view)   # nothing may be drawn outside the view
        surface.fill(self.background, view)
        map_x, map_y = camera.to_screen(0, 0)
        surface.blit(self.map_image, (view.x + map_x, view.y + map_y))

        # Draw things higher on the screen first, so the ones in front overlap them.
        for feet_x, feet_y, image, *rest in sorted(things, key=lambda thing: thing[1]):
            lift = rest[0] if rest else 0
            x, y = camera.to_screen(feet_x, feet_y)
            surface.blit(image, image.get_rect(midbottom=(view.x + x, view.y + y - 3 - lift)))

        surface.blit(self.cap_image, (view.x + map_x, view.y + map_y))
        surface.set_clip(None)
