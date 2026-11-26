"""The weapon a character holds in its hand, and how it attacks with it (owner: A).

The class art (knight, wizard, elf) has no attack pictures, and a weapon is one still
picture. So attacks are animated in code, with the weapon the player has equipped:

  melee  the weapon is raised and swung down in an arc, with a white slash in front of it
  bow    the bow stays up while an arrow flies to the enemy
  staff  the staff is raised while a glowing bolt flies to the enemy

Which style a weapon uses is its "attack" value in data/items.json (melee if it has none).
How it is held (where the hand grips it, how big it is drawn, how it leans) is in data/weapon_grips.json:
a sword is held at the handle, a staff a bit above its middle, a bow upright at arm's length.
An attack has three parts, timed like a hand-drawn attack animation: wind up, strike, recover.
All turned and mirrored pictures are made once when the weapon is created, never while the game runs.
"""
import pygame

from core import assets
from dungeon import sprites
from systems import items
from systems.player import load_data

SWING_ANGLES = [40, 55, 10, -40, -95, -120]    # melee: raise behind the shoulder, then swing forward

# When things happen during an attack; 0.0 is its start and 1.0 its end.
STRIKE_START = 0.35       # the wind-up is over: the swing comes down, the arrow or bolt leaves
IMPACT = 0.6              # the hit lands on the enemy
SLASH_END = 0.8           # the white slash of a melee swing is gone


def grip_rules(item_id, style):
    """How this weapon is held: its style's values from data/weapon_grips.json, with its own changes on top."""
    data = load_data("weapon_grips.json")
    rules = dict(data["styles"][style])
    rules.update(data["weapons"].get(item_id, {}))
    if rules.get("big") and "big_max_length" in rules:
        rules["max_length"] = rules["big_max_length"]
    return rules


def pixel_size(art_length, factor, max_length):
    """How many screen pixels one art pixel of the weapon gets: a whole number from 1 to factor.

    factor is how much the characters are scaled (3 on the map, 4 in fights). A weapon longer than
    max_length gets a smaller whole number, so it shrinks but its pixels stay sharp squares.
    """
    if art_length <= max_length:
        return factor
    return max(1, min(factor, round(factor * max_length / art_length)))


def _turned(image, angle, grip=0.0):
    """Turn a weapon picture around the point where the hand holds it.

    grip: where the hand is, as a share of the weapon's length from its bottom end
    (0.0 = the very bottom, 0.5 = the middle). pygame turns a picture around its centre,
    so the weapon is first put on a bigger see-through square with the grip point exactly
    in the centre; turning that square then turns the weapon around the hand.
    """
    width, height = image.get_size()
    pivot_y = height - round(height * grip)              # from the top of the picture
    side = 2 * max(pivot_y, height - pivot_y, width) + 2
    square = pygame.Surface((side, side), pygame.SRCALPHA)
    square.blit(image, (side // 2 - width // 2, side // 2 - pivot_y))   # the grip lands on the centre
    return pygame.transform.rotate(square, angle)


def _mirrored(image):
    return pygame.transform.flip(image, True, False)


def _both_sides(image):
    """(the picture for facing right, the picture for facing left)."""
    return image, _mirrored(image)


def _slash_picture(factor):
    """A white crescent, like the trail of a fast blade. Drawn small, then scaled up like all art."""
    small = pygame.Surface((14, 20), pygame.SRCALPHA)
    pygame.draw.ellipse(small, (255, 255, 255, 235), (0, 0, 14, 20))
    pygame.draw.ellipse(small, (0, 0, 0, 0), (-5, 1, 14, 18))       # cut the inside away: a crescent stays
    return assets.scale_up(small, factor)


def _bolt_picture(color, factor):
    """A small glowing ball for staffs, in the weapon's own colour with a white middle."""
    small = pygame.Surface((7, 7), pygame.SRCALPHA)
    bright = tuple(min(255, c + 70) for c in color)
    pygame.draw.circle(small, (*color, 150), (3, 3), 3)
    pygame.draw.circle(small, bright, (3, 3), 2)
    small.set_at((3, 3), (255, 255, 255))
    return assets.scale_up(small, factor)


def _arrow_picture(factor):
    """The arrow art points up; an arrow in flight points forward (to the right)."""
    arrow = assets.load_sprite("effect_arrow", factor)
    if arrow is None:
        return _bolt_picture((230, 220, 200), factor)       # no arrow art: a pale bolt instead
    turned = pygame.transform.rotate(arrow, -90)
    return turned.subsurface(turned.get_bounding_rect()).copy()


class HeldWeapon:
    def __init__(self, item_id, factor):
        """item_id: an item id from data/items.json. factor: how much bigger than the art (3 or 4)."""
        self.factor = factor
        try:
            item = items.get_item(item_id)
        except KeyError:
            item = {}                                      # art without an item entry: a plain melee weapon
        self.style = item.get("attack", "melee")
        rules = grip_rules(item_id, self.style)
        self.hand_offset = tuple(rules["hand"])            # art pixels: in front of the body, above the feet
        art = assets.load_sprite(f"weapon_{item_id}", factor=1)
        self.has_art = art is not None                     # no weapon_<id>.png: nothing is drawn
        if not self.has_art:
            return
        bounds = art.get_bounding_rect()
        if bounds.width and bounds.height:
            art = art.subsurface(bounds).copy()            # cut off empty space, so the grip is measured on the weapon itself
        self.pixel = pixel_size(art.get_height(), factor, rules["max_length"])
        image = assets.scale_up(art, self.pixel)
        grip = rules["grip"]
        self.held = _both_sides(_turned(image, rules["hold_angle"], grip))
        if self.style == "melee":
            swing = [_turned(image, angle, grip) for angle in SWING_ANGLES]
            self.swing = (swing, [_mirrored(frame) for frame in swing])
            self.slash = _both_sides(_slash_picture(factor))
            self.projectile = None
        else:
            self.raised = _both_sides(_turned(image, rules.get("raised_angle", rules["hold_angle"]), grip))
            picture = _arrow_picture(factor) if self.style == "bow" else _bolt_picture(tuple(item.get("color", (150, 170, 230))), factor)
            self.projectile = _both_sides(picture)          # what flies to the enemy

    def image(self, facing_left, swing=None):
        """swing: None while just holding it, or 0.0 to 1.0 for how far the attack has gone."""
        side = 1 if facing_left else 0
        if swing is None:
            return self.held[side]
        if self.style != "melee":
            return self.raised[side]
        frames = self.swing[side]
        return frames[min(int(swing * len(frames)), len(frames) - 1)]

    def hand(self, feet_x, feet_y, facing_left):
        """Where the hand is, given the point the character stands on."""
        direction = -1 if facing_left else 1
        hand_x, hand_y = self.hand_offset
        return feet_x + direction * hand_x * self.factor, feet_y - hand_y * self.factor

    def thing(self, feet_x, feet_y, facing_left):
        """The held weapon as an entry for DungeonRenderer.draw(): (x, y, image, lift).

        y is one pixel below the feet, so the weapon is drawn just after (in front of)
        its owner; lift then moves the picture up so its handle sits in the hand.
        """
        image = self.image(facing_left)
        hand_x, hand_y = self.hand(feet_x, feet_y, facing_left)
        sort_y = feet_y + 1
        lift = sort_y - (hand_y + image.get_height() // 2) - 3   # 3 = the renderer's own small lift
        # (the turned picture has the grip point in its centre, so its centre goes on the hand)
        return hand_x, sort_y, image, lift

    def draw(self, surface, feet, facing_left, swing=None):
        """Draw the weapon straight onto a surface (fight screen, class select)."""
        image = self.image(facing_left, swing)
        hand_x, hand_y = self.hand(*feet, facing_left)
        surface.blit(image, image.get_rect(center=(hand_x, hand_y)))
        if self.style == "melee" and swing is not None and STRIKE_START <= swing < SLASH_END:
            direction = -1 if facing_left else 1
            slash = self.slash[1 if facing_left else 0]
            center = (hand_x + direction * 9 * self.factor, hand_y - 2 * self.factor)
            surface.blit(slash, slash.get_rect(center=center))

    def draw_projectile(self, surface, start, target, facing_left, swing):
        """Draw the arrow or bolt on its way from `start` (the hand) to `target` (the enemy).

        It leaves when the strike starts and arrives at the moment of impact.
        Melee weapons have no projectile, so this draws nothing for them.
        """
        if self.projectile is None or swing is None or not STRIKE_START <= swing < IMPACT:
            return
        travelled = (swing - STRIKE_START) / (IMPACT - STRIKE_START)      # 0.0 at the hand, 1.0 at the enemy
        x = start[0] + (target[0] - start[0]) * travelled
        y = start[1] + (target[1] - start[1]) * travelled
        picture = self.projectile[1 if facing_left else 0]
        surface.blit(picture, picture.get_rect(center=(round(x), round(y))))


def held_weapon(player, factor):
    """The HeldWeapon for what the player has equipped, or None (no weapon, or no art for it).

    A class whose own art already has attack pictures (player_<class>_attack_0.png, ...)
    gets None too: its pictures show the weapon, so drawing another one would double it.
    """
    if sprites.has_frames(f"player_{player.class_id}", "attack"):
        return None
    item_id = player.equipped.get("weapon")
    if not item_id:
        return None
    weapon = HeldWeapon(item_id, factor)
    return weapon if weapon.has_art else None
