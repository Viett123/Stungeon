"""Makes the weapon pictures that are recoloured copies of 0x72's art, and copies the spare
weapons from his packs (CC0, see assets/CREDITS.md).

Why recolour: both 0x72 packs have only two staffs and two bows, and the game needed staffs and
bows of every rarity so the mage and the archer have their own weapons (data/items.json "class").

Run from the project folder:  python tools/make_weapon_art.py "A:/Projects/Stungeon Art"
It writes assets/sprites/item_<id>.png and weapon_<id>.png (the same picture twice, like the
other weapons: item_ is the icon in the bag, weapon_ is held in the hand).
"""
import colorsys
import io
import sys
import zipfile
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / "assets" / "sprites"
PACK_2 = "0x72_DungeonTilesetII_v1.7.zip"

# Spare weapons copied as they are: new item id -> file name in DungeonTileset II.
COPIES = {
    "spiked_club": "weapon_baton_with_spikes.png",
    "machete": "weapon_machete.png",
    "double_axe": "weapon_double_axe.png",
    "moon_blade": "weapon_anime_sword.png",
    "hunters_knife": "weapon_knife.png",
}

# Recolours: new item id -> (the game picture it starts from, a list of colour changes).
# A change is (hue_from, hue_to, new_hue, saturation x, value x): every pixel whose hue is
# between hue_from and hue_to (0-360 degrees) gets new_hue, its saturation and brightness scaled.
# Wood on these sprites is orange-brown (hue about 15-40); the staff gems are red or green.
WOOD = (10, 45)
RECOLOURS = {
    "frost_staff":     ("weapon_oak_staff.png",        [(60, 180, 200, 1.0, 1.1), (*WOOD, 210, 0.35, 1.0)]),
    "ember_staff":     ("weapon_apprentice_staff.png", [(345, 360, 28, 1.0, 1.2), (0, 9, 28, 1.0, 1.2), (*WOOD, 0, 0.9, 0.7)]),
    "starlight_staff": ("weapon_oak_staff.png",        [(60, 180, 285, 0.8, 1.2), (*WOOD, 45, 0.8, 1.3)]),
    "elm_longbow":     ("weapon_hunting_bow.png",      [(*WOOD, 40, 0.45, 1.35)]),
    "frost_bow":       ("weapon_short_bow.png",        [(*WOOD, 200, 0.55, 1.2), (345, 360, 200, 0.6, 1.3), (0, 9, 200, 0.6, 1.3)]),
    "sunfire_bow":     ("weapon_hunting_bow.png",      [(*WOOD, 48, 0.95, 1.35)]),
}


def in_range(hue, low, high):
    return low <= hue <= high


def recolour(surface, changes):
    out = surface.copy()
    for x in range(out.get_width()):
        for y in range(out.get_height()):
            r, g, b, a = out.get_at((x, y))
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s < 0.15:              # greys, black outline and white shine stay as they are
                continue
            for low, high, new_hue, s_times, v_times in changes:
                if in_range(h * 360, low, high):
                    nr, ng, nb = colorsys.hsv_to_rgb(new_hue / 360, min(1, s * s_times), min(1, v * v_times))
                    out.set_at((x, y), (round(nr * 255), round(ng * 255), round(nb * 255), a))
                    break
    return out


def save(surface, item_id):
    for prefix in ("item_", "weapon_"):
        pygame.image.save(surface, str(SPRITES / f"{prefix}{item_id}.png"))


def main(art_folder):
    pygame.init()
    pack = zipfile.ZipFile(Path(art_folder) / PACK_2)
    files = {name.rsplit("/", 1)[-1]: name for name in pack.namelist()
             if "/frames/" in name and "/._" not in name and "__MACOSX" not in name}
    for item_id, file_name in COPIES.items():
        save(pygame.image.load(io.BytesIO(pack.read(files[file_name]))), item_id)
    for item_id, (start, changes) in RECOLOURS.items():
        save(recolour(pygame.image.load(str(SPRITES / start)), changes), item_id)
    print(f"wrote {len(COPIES) + len(RECOLOURS)} weapons")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../Stungeon Art")
