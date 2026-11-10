# Adding art

The game runs without any art files: everything missing is drawn as a simple placeholder in code.
To replace a placeholder, put a PNG with the right name in `assets/sprites/`. No code changes needed.

## Rules

- Pixel art, drawn small. The game makes every sprite 3 times bigger (bosses 4 times).
- Tiles are exactly **16 x 16** pixels.
- Characters are **16 pixels wide** and up to about 24 tall. They stand with their feet at the
  bottom of their tile, so a tall sprite overlaps the tile above it.
- Use a transparent background for characters.
- Only our own art or CC0 art. **List every file in [CREDITS.md](CREDITS.md)** with author, license and link.
- Do not copy art from any commercial game.

## File names the game looks for

| File in `assets/sprites/` | What it is |
|---|---|
| `tile_floor.png` | Floor |
| `tile_wall_front.png` | Front face of a wall (the wall directly above a floor tile) |
| `tile_wall_top.png` | Top of a wall, seen from above |
| `tile_stairs.png` | Stairs down |
| `player_warrior.png`, `player_mage.png`, `player_archer.png` | The player, one per class id in `data/classes.json` |
| `enemy_<id>.png` | An enemy, where `<id>` is its id in `data/enemies.json`, e.g. `enemy_vocab_slime.png` |

A broken image file does not crash the game: it is written to `logs/error.log` and the placeholder is used.
