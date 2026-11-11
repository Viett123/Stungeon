# Credits

List every sprite, font and sound here: file, author, license, link.

## 16x16 DungeonTileset II (v1.7) by 0x72

- Author: 0x72 (Robert)
- License: CC0 1.0 Universal (public domain; free for any use, credit not required)
- Link: https://0x72.itch.io/dungeontileset-ii
- License checked on the page above on 11 Nov 2026.

The files below were copied from the pack's `frames/` folder and renamed. Only `tile_floor_6.png`
is changed: it is the pack's plain floor with the pack's skull drawn on top.
`_N` stands for the frame number: the pack's `..._anim_f0.png` became `..._0.png`, and so on.

| Files in `assets/sprites/` | Name in the pack |
|---|---|
| `tile_floor.png` | `floor_1.png` |
| `tile_floor_0.png` to `tile_floor_5.png` | `floor_2.png` to `floor_7.png` |
| `tile_floor_6.png` | `floor_1.png` + `skull.png` (combined) |
| `tile_wall_front.png` | `wall_mid.png` |
| `tile_wall_front_0.png`, `_1.png`, `_2.png` | `wall_banner_red.png`, `wall_hole_1.png`, `wall_hole_2.png` |
| `tile_wall_cap.png` | `wall_top_mid.png` |
| `tile_wall_side_left.png`, `tile_wall_side_right.png` | `wall_outer_mid_left.png`, `wall_outer_mid_right.png` |
| `tile_wall_corner_left.png`, `tile_wall_corner_right.png` | `wall_outer_top_left.png`, `wall_outer_top_right.png` |
| `tile_stairs.png` | `floor_ladder.png` |
| `chest_N.png` | `chest_full_open_anim_fN.png` |
| `player_warrior_idle_N`, `_run_N`, `_hit_N` | `knight_m_idle_anim_fN`, `knight_m_run_anim_fN`, `knight_m_hit_anim_fN` |
| `player_mage_idle_N`, `_run_N`, `_hit_N` | `wizzard_m_...` (same three animations) |
| `player_archer_idle_N`, `_run_N`, `_hit_N` | `elf_m_...` (same three animations) |
| `enemy_vocab_slime_idle_N` | `swampy_anim_fN` |
| `enemy_article_goblin_idle_N`, `_run_N` | `goblin_idle_anim_fN`, `goblin_run_anim_fN` |
| `enemy_plural_bat_idle_N`, `_run_N` | `imp_idle_anim_fN`, `imp_run_anim_fN` |
| `enemy_grammar_ghost_idle_N` | `necromancer_anim_fN` |
| `enemy_boss_floor_1_idle_N`, `_run_N` | `doc_idle_anim_fN`, `doc_run_anim_fN` |
| `enemy_boss_floor_2_idle_N`, `_run_N` | `orc_shaman_idle_anim_fN`, `orc_shaman_run_anim_fN` |
| `enemy_boss_floor_3_idle_N`, `_run_N` | `chort_idle_anim_fN`, `chort_run_anim_fN` |
| `item_small_potion.png` | `flask_red.png` |
| `item_tonic.png` | `flask_blue.png` |
| `item_old_sword.png`, `weapon_old_sword.png` | `weapon_rusty_sword.png` |
| `item_apprentice_staff.png`, `weapon_apprentice_staff.png` | `weapon_red_magic_staff.png` |
| `item_knight_sword.png`, `weapon_knight_sword.png` | `weapon_knight_sword.png` |
| `item_war_axe.png`, `weapon_war_axe.png` | `weapon_axe.png` |
| `item_oak_staff.png`, `weapon_oak_staff.png` | `weapon_green_magic_staff.png` |
| `item_big_potion.png` | `flask_big_red.png` |

## 16x16 Dungeon Walls Reconfig by aekae13

- Author: aekae13 (a reworking of safwyl's "16x16 Dungeon Autotile Remix", itself based on 0x72's tileset)
- License: CC0 (the pack's page says it can be used for anything, credit not required)
- Link: https://aekae13.itch.io/16x16-dungeon-walls-reconfig
- License checked on 11 Nov 2026. The downloaded zip itself has no license file.

| Files in `assets/sprites/` | Name in the pack |
|---|---|
| `item_hunting_bow.png`, `weapon_hunting_bow.png` | `bow/bow.png` |
| `effect_hit_0.png` to `effect_hit_4.png` | `bow/effect/hit0.png` to `hit4.png` |

Not used yet: the pack's wall sheet (a different, darker wall set) and `bow/arrow.png`.

## Custom dungeon 16x16 tileset (jungle and desert) by Omniboy

- Author: Omniboy (recolours and additions based on 0x72's tileset)
- License: CC0. The pack's readme only says "free"; the author confirms CC-0 in the comments of the page below.
- Link: https://omniboy.itch.io/custom-dungeon-16x16-tileset
- License checked on 11 Nov 2026.

The pack is two sheets. The tiles below were cut out of them (16 x 16 each) and saved as single files.
The corner pieces are the bottom 4 pixel rows of the side lines.

| Files | Cut from |
|---|---|
| `assets/sprites/jungle/*.png` (20 files) | `omnibo_jungledungeon - copia.png` |
| `assets/sprites/desert/*.png` (20 files) | `omnibo_dessert_dungeon.png` |

Not used yet from these sheets: fountains, totems, spike traps, the wall monster.

## Still drawn in code (no art file yet)

- All armour and accessory items (hood, vest, trousers, boots, ring, charm): none of the packs has such art.
- All move icons.
- All menu frames, bars and slots (`ui/theme.py`).
- The font is pygame's built-in font.
