# Adding art

The game runs without any art files: everything missing is drawn as a simple placeholder in code.
To replace a placeholder, put a PNG with the right name in `assets/sprites/`. No code changes needed.

## Rules

- Pixel art, drawn small. The game makes every sprite 3 times bigger (bosses 4 times).
- Tiles are exactly **16 x 16** pixels.
- Characters are **16 pixels wide** and up to about 28 tall. They stand with their feet at the
  bottom of their tile, so a tall sprite overlaps the tile above it.
- Draw characters **facing right**. The game mirrors them when they walk left.
- An animation is several files with the same name and a number at the end, starting at 0.
  All frames of one animation must be the same size. Any number of frames works.
- Use a transparent background for characters.
- Only our own art or CC0 art. **List every file in [CREDITS.md](CREDITS.md)** with author, license and link.
- Do not copy art from any commercial game.

## File names the game looks for

| File in `assets/sprites/` | What it is |
|---|---|
| `tile_floor.png` | Floor |
| `tile_floor_0.png` ... `tile_floor_31.png` | Optional other floor pictures (cracks, a skull). Each one is used on about 1 tile in 32; the rest use `tile_floor.png` |
| `tile_wall_front.png` | The brick face of a wall |
| `tile_wall_front_0.png` ... `tile_wall_front_19.png` | Optional other brick pictures (a banner, a hole). Each one is used on about 1 brick in 20 |
| `tile_wall_cap.png` | The stone strip on top of a brick face. Mostly see-through, with the strip along the bottom edge |
| `tile_wall_side_left.png`, `tile_wall_side_right.png` | The thin line beside a room: on the right edge of the picture for `left`, on the left edge for `right` |
| `tile_wall_corner_left.png`, `tile_wall_corner_right.png` | The small piece where a side line meets a cap |
| `tile_stairs.png` | Stairs down |
| `chest_0.png`, `chest_1.png`, ... | A chest opening: the first picture is closed, the last is fully open |
| `player_<class>_idle_0.png`, `_1.png`, ... | The player standing, one set per class id in `data/classes.json` (`warrior`, `mage`, `archer`) |
| `player_<class>_run_0.png`, ... | The player walking. Without these, the idle pictures are used |
| `player_<class>_hit_0.png`, ... | The player being hurt (shown in a fight) |
| `enemy_<id>_idle_0.png`, ... and `enemy_<id>_run_0.png`, ... | An enemy, where `<id>` is its id in `data/enemies.json`, e.g. `enemy_vocab_slime_idle_0.png` |
| `player_<class>.png`, `enemy_<id>.png` | One still picture, used only if there are no `_idle_` pictures |
| `item_<id>.png` | An item's icon for the bag and the shop, where `<id>` is its id in `data/items.json`, e.g. `item_small_potion.png`. Art taller than 16 pixels is drawn smaller so it fits the slot |
| `icon_<id>.png` | A move's icon (16 x 16) for the hotbar, where `<id>` is its id in `data/moves.json`, e.g. `icon_fireball.png` |

The frames, bars and slots of the menus are drawn in code (`ui/theme.py`), so they need no art files.
A real font is still missing: the game uses pygame's built-in font until someone picks a CC0 pixel font.

A broken image file does not crash the game: it is written to `logs/error.log` and the placeholder is used.
