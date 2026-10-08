# renewal-world

Renewal's new lands, in pre-renewal.

Pre-renewal rAthena already loads every renewal map, and the client already
has them. Nothing leads there. This mod adds the way in, where renewal puts
it, so the world grows past its old edges without a warper:

| Region | Way in | Maps |
|---|---|---|
| Bifrost, Mora | the bridge north of Splendide; the Dimensional Gap from Midgard Camp or the Morocc field | bif_fild01-02, mora, dali |
| El Dicastes | Kamidal Mountain from Bifrost via the Dimensional Gap; the Scaraba Hole from Manuk | dic_fild01-02, dicastes01-02, dic_in01, dic_dun01-03 |
| Eclage | a portal from the Mora field (bif_fild02) | ecl_fild01, eclage, ecl_hub01, ecl_in01-03, ecl_tdun01-04 |
| Verus | the east end of Juperos | ver_eju, ver_tunn, verus01-04 |
| Dewata, Port Malaya, Malangdo, Rockridge | ships on Alberta's piers | dewata, dew_*, malaya, ma_*, malangdo, mal_*, harboro1-2, har_in01, rockrdg1-2, rockmi1-2 |
| New dungeon floors | Niflheim town; one floor below the deepest of Izlude, Abyss Lakes, Einbroch mine and Magma dungeons | nif_dun01-02, iz_dun05, abyss_04, ein_dun03, mag_dun03 |

**This version opens the way only.** The new maps have no monsters, shops,
Kafras or quests yet. Monsters with pre-renewal stats are the next step.
Until then it is a world to walk, not to level in. You cannot save in the new
towns, so a Butterfly Wing takes you home.

## Staged areas

Another 77 maps already have their own portals, joined to each other and to
the open maps, but **nothing leads in yet**. Renewal reaches them only through
an episode quest, an instance or a ship that has no place in pre-renewal yet.
Opening one later only takes a way in: a gate, or one portal turned on. The
build checks that none of them can be reached from the old world until then.

| Area | Maps |
|---|---|
| Lasagna | lasagna, lasa_fild01-02, lasa_in01, conch_in, lasa_dun01-03, lasa_dun_q |
| Bios Island | ba_maison, ba_in01, ba_lost, ba_lib, ba_bath, ba_2whs01-02, ba_pw01-03 |
| Rudus | sp_os, sp_cor, sp_rudus, sp_rudus2-4 |
| Amicitia | amicitia1-2 |
| Wolfchev's laboratory | lhz_dun04, que_lhz |
| Nightmare dungeons | moc_prydn1-2, c_tower2_-3_, gl_chyard_, gl_cas01_-02_, treasure_n1-2, lhz_dun_n, lhz_d_n2 |
| Illusion dungeons | ant_d02_i, com_d02_i, ein_d02_i, gef_d01_i, ice_d03_i, iz_d04_i, iz_d05_i, pay_d03_i, tur_d03_i, tur_d04_i, prt_mz03_i |
| Episode areas | moro_cav, moro_vol, dali02; gw_fild01-02, wolfvill, oz_dun01-02; for_dun01-02, t_garden; slabw01, que_swat; un_bunker, un_myst, un_bk_q; ma_scene01; ecl_in04 |
| Prontera Castle | prt_cas, prt_cas_q, prt_lib, prt_lib_q, prt_q, prt_prison, prt_pri00, prt_elib |

A GM can `@warp` into any of them to look around. Some have no portal back
out, because renewal leaves through a quest NPC: use a Butterfly Wing.

Brasilis is not here on purpose. rAthena ships a pre-renewal Brasilis that is
switched off, and a mod turns it on with `stock-npc.txt`. Copying renewal's
portals would clash with it.

## How it joins the old world

Every portal between the new maps, and from them to the old world, is copied
from rAthena's renewal scripts unchanged. Where renewal puts the way in behind
a quest, an instance or a ship, the mod has a **gate** instead: an NPC at the
same spot who asks once and sends you on, free.

- The ships stand on Alberta's piers beside the old ones, because pre-renewal
  Alberta has its classic layout and renewal's spots are in the water.
- The Hazy Forest instance between Bifrost and Mora is a Log Tunnel at each
  end.
- The checkpoints into Eclage, El Dicastes and inner Verus let you through
  without the episode quests.

The maps' town, no-memo, no-teleport and similar flags are copied from
renewal too.

## Where things are defined

Everything comes from two files in
[`registry/tools/renewal-world/`](../../tools/renewal-world/):

- `maps.csv`: the maps the mod covers, by region, each `open` (with a way in)
  or `staged` (joined to its neighbours, no way in yet). A renewal portal to a
  map that is not listed, or into a staged map from outside, is left out.
- `gates.csv`: one row per gate, with where it stands, what it looks like and
  where it sends you.

`build.py` beside them reads rAthena's renewal scripts and writes the mod's
three scripts in `npc/`. It refuses to write if:

- a gate stands where pre-renewal has no walkable cell;
- a gate or portal crowds one pre-renewal already has;
- a name is taken;
- an open map has no way in from the old world, or no way back;
- a staged map can be reached from the old world.

```
python3 registry/tools/renewal-world/build.py --rathena ../rathena          # check, show what changes
python3 registry/tools/renewal-world/build.py --rathena ../rathena --write  # write npc/
python3 scripts/mod-index.py
```

Point `--rathena` at a checkout of the pinned rAthena commit
(`config/VENDOR_PINS`). After a pin bump, run it again: `--check` fails when
the copied portals have changed.
