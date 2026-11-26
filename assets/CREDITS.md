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
| `enemy_grammar_ghost_idle_N` | `necromancer_anim_fN` |
| `enemy_abbrev_imp_idle_N`, `_run_N` | `imp_idle_anim_fN`, `imp_run_anim_fN` |
| `enemy_while_wisp_idle_N` | `ice_zombie_anim_fN` |
| `npc_merchant_idle_N` (the shop owner) | `dwarf_m_idle_anim_fN` |
| `enemy_debate_gargoyle_idle_N`, `_run_N` | `masked_orc_idle_anim_fN`, `masked_orc_run_anim_fN` |
| `enemy_boss_floor_1_idle_N`, `_run_N` | `doc_idle_anim_fN`, `doc_run_anim_fN` |
| `enemy_boss_floor_2_idle_N`, `_run_N` | `orc_shaman_idle_anim_fN`, `orc_shaman_run_anim_fN` |
| `enemy_boss_floor_3_idle_N`, `_run_N` | `chort_idle_anim_fN`, `chort_run_anim_fN` |
| `enemy_mini_floor_1_idle_N`, `_run_N` | `big_zombie_idle_anim_fN`, `big_zombie_run_anim_fN` |
| `enemy_mini_floor_2_idle_N`, `_run_N` | `ogre_idle_anim_fN`, `ogre_run_anim_fN` |
| `enemy_mini_floor_3_idle_N`, `_run_N` | `big_demon_idle_anim_fN`, `big_demon_run_anim_fN` |
| `tile_spikes.png` | `floor_spikes_anim_f3.png` |
| `item_old_sword.png`, `weapon_old_sword.png` | `weapon_rusty_sword.png` |
| `item_apprentice_staff.png`, `weapon_apprentice_staff.png` | `weapon_red_magic_staff.png` |
| `item_katana`, `item_mace`, `item_spear`, `item_cleaver`, `item_golden_sword`, `item_lavish_sword`, `item_duel_sword` (and the same with `weapon_`) | `weapon_katana`, `weapon_mace`, `weapon_spear`, `weapon_cleaver`, `weapon_golden_sword`, `weapon_lavish_sword`, `weapon_duel_sword` |
| `item_short_bow.png`, `weapon_short_bow.png` | `weapon_bow_2.png` |
| `item_knight_sword.png`, `weapon_knight_sword.png` | `weapon_knight_sword.png` |
| `item_war_axe.png`, `weapon_war_axe.png` | `weapon_axe.png` |
| `item_oak_staff.png`, `weapon_oak_staff.png` | `weapon_green_magic_staff.png` |

## Pixel Art Sprite Mixer by KingBell (reference only)

- Author: KingBell. Link: https://kingbell.itch.io/pixel-sprite-mixer
- **No file from this pack is in the game.** For a short time the three classes used frames cut from its
  free hero sheet (see the git history of branch `art/kingbell-classes`); the team preferred the
  knight, wizard and elf from 0x72's pack, so those came back.
- What we took from it is an idea, not pictures: we watched how its attack animations are timed
  (wind up, strike, recover; when the slash and the hit appear) and built our own attacks in code
  with that timing (`dungeon/weapon.py`, `combat/combat_scene.py`).
- The author is still named on the Credits screen as a thank-you.
- If its sprites are used again: the pack is CC BY 4.0 (credit with a link is required), its license
  file says not to use it in AI, and the author told the project lead (Viet) in November 2026 that
  use in this game is fine. Keep that message.

## DungeonUI by 0x72

- Author: 0x72 (Robert)
- License: CC0 (stated in the pack's description)
- Link: https://0x72.itch.io/dungeonui
- License checked on 14 Nov 2026.

No file from this pack is in the game any more. `ui_frame.png` used to be its small square frame
(24 x 24 pixels, at x 24, y 72 of `dungeonui.v1.png`); it was replaced by our own frames (see below).

## Item icons: drawn by us

Drawn mainly by **conchuotbiluoc** (GitHub: ahihilili299-wq), 16 x 16 each; handed over as
`new_asset.zip` and `potion.zip` on 26 Nov 2026, plus the new Big Potion and Tonic drawings.
`item_cloth_hood.png` came from the first art branch (`c/new_asset`, commit d8717a9 by Tien Le).
Also on the in-game Credits screen (`data/credits.json`).
They replace the 0x72 pictures where an item already had one. Nothing to license.

| File in `assets/sprites/` | Drawn as |
|---|---|
| `item_small_potion.png`, `item_big_potion.png`, `item_tonic.png` | `potion/small_potion.png`, `potion/big_potion.png`, and a later Tonic drawing |
| `item_copper_ring.png`, `item_gold_ring.png` | `copper_ring.png`, `gold_ring.png` |
| `item_leather_vest.png`, `item_wool_trousers.png`, `item_worn_boots.png` | `leather_vest.png`, `wool_trousers.png`, `worn boots.png` |
| `item_lucky_charm.png` | `lucky_charm.png` |
| `item_iron_armor.png`, `item_iron_helmet.png` (new items) | `armor.png`, `armor_head.png` |
| `item_cloth_hood.png` | `cloth_hood.png` |

## UI frames: drawn by us

- `assets/sprites/ui_frame.png` (stone floors), `assets/sprites/desert/ui_frame.png` and
  `assets/sprites/jungle/ui_frame.png`: drawn by Viet (project lead), 24 x 24 pixels each, in the same
  layout as 0x72's frame. Nothing to license.

## 16x16 Dungeon Tileset (v5) by 0x72

- Author: 0x72 (Robert). This is the older sister pack of DungeonTileset II.
- License: CC0 1.0 Universal (the page says it can be used for anything, credit not required)
- Link: https://0x72.itch.io/16x16-dungeon-tileset
- License checked on 14 Nov 2026.

| Files in `assets/sprites/` | Name in the pack's `items/` folder |
|---|---|
| `torch_0.png` to `torch_7.png` | `torch_1.png` to `torch_8.png` |
| `chest_golden_0.png`, `chest_golden_1.png` | `chest_golden_closed.png`, `chest_golden_open_full.png` |
| `npc_merchant.png` | `npc_merchant.png` (only used if the dwarf's animation is missing) |
| `enemy_plural_bat.png` | `monster_bat.png` |
| `item_ruby_sword.png`, `weapon_ruby_sword.png` | `weapon_sword_ruby.png` |
| `item_golden_dagger.png`, `weapon_golden_dagger.png` | `weapon_dagger_golden.png` |
| `item_emerald_sword.png`, `weapon_emerald_sword.png` | `weapon_sword_emerald.png` |
| `item_sledgehammer.png`, `weapon_sledgehammer.png` | `weapon_sledgehammer.png` |

Not used yet from this pack: doors, columns, boxes, gargoyle fountains, about 40 more monsters and
NPCs (one picture each, no animation), 20 more weapons.

## 16x16 Dungeon Walls Reconfig by aekae13

- Author: aekae13 (a reworking of safwyl's "16x16 Dungeon Autotile Remix", itself based on 0x72's tileset)
- License: CC0 (the pack's page says it can be used for anything, credit not required)
- Link: https://aekae13.itch.io/16x16-dungeon-walls-reconfig
- License checked on 11 Nov 2026. The downloaded zip itself has no license file.

| Files in `assets/sprites/` | Name in the pack |
|---|---|
| `item_hunting_bow.png`, `weapon_hunting_bow.png` | `bow/bow.png` |
| `effect_hit_0.png` to `effect_hit_4.png` | `bow/effect/hit0.png` to `hit4.png` |
| `effect_arrow.png` | `bow/arrow.png` |

Not used yet: the pack's wall sheet (a different, darker wall set).

## Custom dungeon 16x16 tileset (jungle and desert) by Omniboy

- Author: Omniboy (recolours and additions based on 0x72's tileset)
- License: CC0. The pack's readme only says "free"; the author confirms CC-0 in the comments of the page below.
- Link: https://omniboy.itch.io/custom-dungeon-16x16-tileset
- License checked on 11 Nov 2026.

The pack is two sheets. The tiles below were cut out of them (16 x 16 each) and saved as single files.
The corner pieces are the bottom 4 pixel rows of the side lines.

| Files | Cut from |
|---|---|
| `assets/sprites/jungle/*.png` (21 files, with the spikes) | `omnibo_jungledungeon - copia.png` |
| `assets/sprites/desert/*.png` (21 files, with the spikes) | `omnibo_dessert_dungeon.png` |

Not used yet from these sheets: fountains, totems, the wall monster.

## Still drawn in code (no art file yet)

- All move icons.
- Bars, slots and buttons (`ui/theme.py`). The panel borders now come from `ui_frame.png`.
- Nothing else: the font is now a real pixel font (see Fonts).

## Fonts

Both are from Google Fonts' GitHub (https://github.com/google/fonts), downloaded on 26 Nov 2026.
License: SIL Open Font License 1.1 (free to use and ship with a game; the license file must go with
the font, so it is in `assets/fonts/` next to it). Both can draw English, German and Vietnamese.

| File in `assets/fonts/` | Font | Author | License file |
|---|---|---|---|
| `Tiny5.ttf` (the file `Tiny5[BLED,JITT,ROND,wdth,wght].ttf`, renamed) | Tiny5 | The Tiny5 Project Authors (Stefan Schmidt), https://github.com/Gissio/font_tiny5 | `OFL-Tiny5.txt` |
| `VT323-Regular.ttf` | VT323 | The VT323 Project Authors (Peter Hull) | `OFL-VT323.txt` |

## Sound and music: made by us, in code

Every file in `assets/sounds/` (19 effects and 4 music loops) is made by `tools/make_sounds.py`
from the recipes in `data/sounds.json`. Nothing is downloaded, so there is nothing to license or credit.
