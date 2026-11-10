"""Draws a floor and the characters on it (owner: A).

The floor never changes while you walk on it, so it is drawn ONCE onto one big image
(self.map_image) when the floor starts. Every frame we only copy the visible part of
that image to the screen and then draw the characters on top. That is much faster than
drawing a thousand tiles 60 times a second.
"""
import pygame

from core import settings
from dungeon import sprites, tiles

TILE = settings.TILE
SHADOW_HEIGHT = 12            # pixels of shadow a wall casts on the floor below it
SHADOW_COLOR = (0, 0, 0, 70)  # black, mostly see-through

_SPRITE_FOR_LOOK = {
    tiles.LOOK_WALL_FRONT: "tile_wall_front",
    tiles.LOOK_WALL_TOP: "tile_wall_top",
    tiles.LOOK_STAIRS: "tile_stairs",
}


class DungeonRenderer:
    def __init__(self, floor):
        self.floor = floor
        self.world_w = floor.width * TILE
        self.world_h = floor.height * TILE
        self.map_image = self._draw_map()

    # --- once per floor ----------------------------------------------------
    def _draw_map(self):
        image = pygame.Surface((self.world_w, self.world_h))
        image.fill(sprites.VOID)
        shadow = pygame.Surface((TILE, SHADOW_HEIGHT), pygame.SRCALPHA)
        shadow.fill(SHADOW_COLOR)
        grid = self.floor.grid
        for y in range(self.floor.height):
            for x in range(self.floor.width):
                look = tiles.tile_look(grid, x, y)
                if look == tiles.LOOK_VOID:
                    continue
                image.blit(self._tile_image(look, x, y), (x * TILE, y * TILE))
                if tiles.in_wall_shadow(grid, x, y):
                    image.blit(shadow, (x * TILE, y * TILE))
        return image

    def _tile_image(self, look, x, y):
        if look == tiles.LOOK_FLOOR:
            # A different variant per position, so the floor does not look like a repeated stamp.
            return sprites.tile_sprite("tile_floor", variant=(x * 7 + y * 13) % 8)
        return sprites.tile_sprite(_SPRITE_FOR_LOOK[look])

    # --- every frame -------------------------------------------------------
    def draw(self, surface, view, camera, characters):
        """Draw the visible part of the floor into the rectangle `view` on `surface`.

        characters: list of (tile_x, tile_y, image). They stand with their feet at the
        bottom of their tile; a tall image overlaps the tile above it.
        """
        surface.set_clip(view)   # nothing may be drawn outside the view (e.g. over the status bar)
        surface.fill(sprites.VOID, view)
        map_x, map_y = camera.to_screen(0, 0)
        surface.blit(self.map_image, (view.x + map_x, view.y + map_y))

        # Draw characters higher on the screen first, so the ones in front overlap them.
        for tile_x, tile_y, image in sorted(characters, key=lambda c: c[1]):
            feet_x, feet_y = camera.to_screen(tile_x * TILE + TILE // 2, (tile_y + 1) * TILE)
            rect = image.get_rect(midbottom=(view.x + feet_x, view.y + feet_y - 3))
            surface.blit(image, rect)
        surface.set_clip(None)
