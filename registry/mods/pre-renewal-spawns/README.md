# pre-renewal-spawns

Renewal, with the monsters where pre-renewal put them.

Every map that pre-renewal had gets the pre-renewal spawn list: the same
monsters, the same numbers and the same respawn times. Maps that only renewal
has, such as Brasilis, Dewata, Verus or the illusion dungeons, keep their
renewal spawns.

The monsters are still the renewal ones. A Poring has its renewal level,
stats and drops. Only *which* monsters appear on a map, and how many, comes
from pre-renewal. The mod does nothing on a pre-renewal server.

## What it changes, in numbers

On the 274 maps that have spawns in both eras, rAthena's stock scripts put
out:

| | spawn lines | monsters |
|---|---|---|
| pre-renewal | 3,199 | 36,783 |
| renewal | 2,497 | 48,670 |

Renewal is **denser** on 258 of those 274 maps. Its fields often carry two
or three times as many monsters (`cmd_fild07`: 39 → 220, `ra_fild03`:
66 → 239). So on most maps this mod gives you *fewer* monsters, and
different ones. To raise the count as well, use it alongside
[map-spawn-rate](../map-spawn-rate). The rates scale the pre-renewal lines
this mod loads.

A map counts as "pre-renewal" when the pre-renewal spawn scripts spawn
something on it. That covers every field and dungeon, and the towns where
pre-renewal kept a stray Wild Rose or Thief Bug. A map with no pre-renewal
spawns is left as renewal has it.

## How it works

Server-side only, using stock rAthena script commands. It needs no rAthena
extension.

1. The mod ships every pre-renewal spawn file as `npc/pre-re/...`, loaded at
   start-up like any mod script.
2. When the server is up, `npc/pre_renewal_spawns.txt` runs
   `@unloadnpcfile` on each renewal spawn file that spawns on a pre-renewal
   map (62 of them). This removes their spawns and any monsters already out.
3. Most of those files also spawn on maps that pre-renewal never had. For
   those maps, the mod carries what is left of each file in `npc/re/...`,
   302 lines in all, so those maps keep their spawns.

A few of those renewal files hold scripts as well: the illusion dungeons'
boss counters, and the timed MVPs on `lhz_dun03`, `lhz_dun04` and
`niflheim`. The mod's copies in `npc/re/` load first and keep their names.
Then the stock copies load under new names and are unloaded with their
files. The map server log names each one once at start-up, and this is
expected:

```
[Warning]: npc_parsename: Duplicate unique name in file 'npc/re/mobs/dungeons/anthell.txt', line'137'. Renaming 'ant_d02_i_boss' to ...
```

A monster that a script summoned at start-up outlives the script, so the mod
clears those maps of script-summoned monsters. Then it restarts the scripts
that summon there. Finally the log confirms the swap:

```
[Debug]: pre-renewal-spawns: replaced 62 renewal spawn files
```

## Limits

- **`navigation-server-monsters` lists both eras' spawns on these maps.**
  It reads the scripts the server loads, plus every mod's, so it sees this
  mod's lines. It cannot see the renewal files being unloaded once the server
  is up.
- The `map-spawn-rate` settings window lists the renewal monsters for each
  map, because its list is built from the stock scripts. The rates still
  apply to what this mod loads.
- `killmonster "<map>","All"` runs on `com_d02_i`, `lhz_dun03`, `lhz_dun04`
  and `niflheim` at start-up. On those four maps, it also removes monsters
  that another mod's script summoned at start-up.

- `@reloadscript` re-reads only rAthena's own script list, so it drops every
  mod's scripts, this one's included, and the renewal spawns come back.
  Restart the server instead.

## Regenerating

Everything under `npc/` is generated from the pinned rAthena by
`registry/tools/pre-renewal-spawns/build_spawns.py`. Rerun it after an
rAthena bump; `--check` fails when the committed files are stale.
