"""The weapon a character holds in its hand, and its swing (owner: A).

The art packs have no attack animations: a weapon is one still picture. So the swing
is made in code by turning that picture around its handle. All turned pictures are
made once when the weapon is created, never while the game runs.
"""
import pygame

from core import assets

IDLE_ANGLE = -30                               # degrees; tilted a little forward while held
SWING_ANGLES = [40, 10, -25, -60, -95, -120]   # from raised behind the shoulder to swung forward
HAND_X = 6                                     # the hand, in art pixels: this far in front of the body...
HAND_Y = 8                                     # ...and this far above the feet


def _turned(image, angle):
    """Turn a weapon picture around its handle (the bottom middle of the picture).

    pygame turns a picture around its centre. So the weapon is first put on a bigger
    see-through square with its handle exactly in the centre; turning that square
    then turns the weapon around its handle.
    """
    width, height = image.get_size()
    square = pygame.Surface((2 * height, 2 * height), pygame.SRCALPHA)
    square.blit(image, (height - width // 2, 0))          # the handle lands on the centre
    return pygame.transform.rotate(square, angle)


def _mirrored(image):
    return pygame.transform.flip(image, True, False)


class HeldWeapon:
    def __init__(self, item_id, factor):
        """item_id: an item id from data/items.json. factor: how much bigger than the art (3 or 4)."""
        self.factor = factor
        image = assets.load_sprite(f"weapon_{item_id}", factor)
        self.has_art = image is not None                   # no weapon_<id>.png: nothing is drawn
        if not self.has_art:
            return
        idle = _turned(image, IDLE_ANGLE)
        swing = [_turned(image, angle) for angle in SWING_ANGLES]
        self.idle = (idle, _mirrored(idle))                # (facing right, facing left)
        self.swing = (swing, [_mirrored(frame) for frame in swing])

    def image(self, facing_left, swing=None):
        """swing: None while just holding it, or 0.0 to 1.0 for how far the swing has gone."""
        side = 1 if facing_left else 0
        if swing is None:
            return self.idle[side]
        frames = self.swing[side]
        return frames[min(int(swing * len(frames)), len(frames) - 1)]

    def hand(self, feet_x, feet_y, facing_left):
        """Where the hand is, given the point the character stands on."""
        direction = -1 if facing_left else 1
        return feet_x + direction * HAND_X * self.factor, feet_y - HAND_Y * self.factor

    def thing(self, feet_x, feet_y, facing_left):
        """The held weapon as an entry for DungeonRenderer.draw(): (x, y, image, lift).

        y is one pixel below the feet, so the weapon is drawn just after (in front of)
        its owner; lift then moves the picture up so its handle sits in the hand.
        """
        image = self.image(facing_left)
        hand_x, hand_y = self.hand(feet_x, feet_y, facing_left)
        sort_y = feet_y + 1
        lift = sort_y - (hand_y + image.get_height() // 2) - 3   # 3 = the renderer's own small lift
        return hand_x, sort_y, image, lift

    def draw(self, surface, feet, facing_left, swing=None):
        """Draw the weapon straight onto a surface (used on the fight screen)."""
        image = self.image(facing_left, swing)
        surface.blit(image, image.get_rect(center=self.hand(*feet, facing_left)))


def held_weapon(player, factor):
    """The HeldWeapon for what the player has equipped, or None (no weapon, or no art for it)."""
    item_id = player.equipped.get("weapon")
    if not item_id:
        return None
    weapon = HeldWeapon(item_id, factor)
    return weapon if weapon.has_art else None
