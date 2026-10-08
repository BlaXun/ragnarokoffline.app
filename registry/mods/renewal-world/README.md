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

- `maps.csv`: the maps the mod opens, by region. A renewal portal to a map
  that is not listed is left out.
- `gates.csv`: one row per gate, with where it stands, what it looks like and
  where it sends you.

`build.py` beside them reads rAthena's renewal scripts and writes the mod's
three scripts in `npc/`. It refuses to write if:

- a gate stands where pre-renewal has no walkable cell;
- a gate or portal crowds one pre-renewal already has;
- a name is taken;
- a listed map has no way in from the old world, or no way back.

```
python3 registry/tools/renewal-world/build.py --rathena ../rathena          # check, show what changes
python3 registry/tools/renewal-world/build.py --rathena ../rathena --write  # write npc/
python3 scripts/mod-index.py
```

Point `--rathena` at a checkout of the pinned rAthena commit
(`config/VENDOR_PINS`). After a pin bump, run it again: `--check` fails when
the copied portals have changed.
