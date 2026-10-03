# waypoint-system

Travel you earn, instead of a free warper.

Waypoint boards stand on 41 fields and dungeon floors, from low-level spots
to end-game ones. Walk there, bring the board what the monsters around it
drop, and it attunes to you. From then on a **Waypoint Keeper** in any town
sends you there for a fee, and the board sends you back to the town you came
from, once per trip.

## Playing it

- **Find a board.** It stands a few steps from where you walk onto the map.
  Talking to it shows what it wants and how many of each you carry.
- **Attune.** Offer the items. They are used up, and the waypoint is yours.
- **Travel.** A Waypoint Keeper stands beside the usual warper spot in every
  major town. Pick *Fields* or *Dungeons*, then a waypoint.
- **Return.** After a keeper sends you out, the board you arrived at offers
  one free trip back to the town you left from.

What a board wants comes from the monsters on its map: the drops you collect
naturally while levelling there. Fields ask for one common drop. Dungeon
floors add a rarer one (0.5–5%), and the highest-level spots ask for more.
Cards, MVP drops, refine ores, gemstones and anything an NPC shop sells are
never asked for.

The fee depends on the waypoint's level and how many maps it is from the
nearest town: 800 zeny for a field next to town, up to a few thousand for a
deep, high-level dungeon. Dungeon floors further down cost a little more.

## Settings

| Setting | Default | What it does |
|---|---|---|
| Waypoints are shared by the whole account | off | Off: each character attunes on its own. On: one character's waypoints work for all of them. Both are always saved, so switching loses nothing. |
| Travel fee (%) | 100 | Scales every fee. 0 makes travel free once attuned. |
| Items to attune (%) | 100 | Scales how many items each board asks for. Never less than one. |
| Keepers list boards you have found | on | Keepers also list boards you visited but did not attune to yet, as a reminder. |

## Both eras

Renewal and pre-renewal have different monsters, drops and levels, so each
has its own generated table (`npc/waypoints_placed.txt`, and
`pre-re/npc/waypoints_placed.txt`, which replaces it in pre-renewal). The
three renewal-only waypoints (Krakatau, Malaya field, Rockridge mine) are
left out of pre-renewal.

## Changing the waypoints

The list and the balance are generated from rAthena's own data by
[`registry/tools/waypoint-system`](../../tools/waypoint-system):

- `waypoints.csv`: one row per waypoint. Add a row to add a waypoint, delete
  one to drop it. The `Id` is permanent, because unlocks are saved under it.
- `towns.csv`: where the keepers stand.
- `build_waypoints.py --write` regenerates both eras' scripts, and
  `--preview balance-preview.csv` writes the fee and items of every waypoint
  for review. The balance knobs are at the top of the script.

## Files

| Path | What it is |
|---|---|
| `npc/waypoints.txt` | the board and keeper templates, and the unlock helpers |
| `npc/waypoints_placed.txt` | generated, renewal: the data, and every board and keeper |
| `pre-re/npc/waypoints_placed.txt` | generated, pre-renewal |
| `System/jobname.lub` | gives the keeper NPC id 19510 its sprite |
| `data/sprite/npc/wp_npc.*` | the keeper's sprite |

The boards use the stock bulletin-board sprite (858).
