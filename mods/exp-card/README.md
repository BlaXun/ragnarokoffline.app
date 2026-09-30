# exp-card

Every monster kill has a small chance to drop an **Exp Card**, bound to the
killer for the standard pickup window. Using the card grants a percentage of
the experience you need for your next level (base and job separately), so it
stays useful whether you're level 12 or 175.

The point: streamline the offline experience without touching per-mob drop
tables. Any mob, any map, one uniform bonus channel.

## How it works, layer by layer

The interesting part is that the mod *does not* modify any mob's drop table.
It hangs off rAthena's kill event and hands out an owned flooritem, using a
new script command (`makeitemowned`) that ships in our rAthena fork.

| Step | Layer | What happens |
|---|---|---|
| A monster dies | rAthena | `OnNPCKillEvent` fires on the top damager (`first_sd`) — stock rAthena behaviour. |
| Roll the chance | `npc/exp_card.txt` | `rand(10000) < .chance` — same roll shape mob drop tables use, in 0.01% units. |
| Drop the card, bound to the killer | `npc/exp_card.txt` | `makeitemowned 30051, 1, "<map>", <x>, <y>;` — no explicit `first_charid`, so it defaults to the attached player's `char_id`. |
| Killer has priority to pick it up | rAthena | `battle.conf`'s `item_first_get_time` window applies, same as regular drops. After it elapses the drop is free for everyone. |
| Player uses the card | `db/item_db.yml` | Item script computes `NextBaseExp * base_pct / 100` and `NextJobExp * job_pct / 100`, calls `getexp`. |

The scaling is what makes the card "always meaningful": the reward is always
some fraction of what you need for the next level, not a fixed number that
either trivialises low levels or vanishes at high levels.

## Settings

**Settings → Mods → exp-card** exposes three numbers, all read through
`F_ModSetting` on each server start (so **Apply** takes effect on the next
restart):

- **Drop chance** (`drop_chance`, default 100 = 1%) — in 0.01% units, matching
  rAthena's drop-rate convention. 1000 is 10%, 10000 is guaranteed.
- **Base exp per card (%)** (`base_pct`, default 5) — percentage of the
  current `NextBaseExp` requirement granted on use.
- **Job exp per card (%)** (`job_pct`, default 5) — percentage of the current
  `NextJobExp` requirement granted on use.

## Requirements

- `requires.app` is **`>=1.3.8`**.
- The server must have the **`makeitem_owned` extension** compiled in and
  registered — that's a rAthena fork commit (branch `makeitem-owned`). The
  mod ships `db/extension_db.yml` that enables it, but on a server without
  the extension registered, `makeitemowned` returns failure and the on-kill
  event logs a one-line error per kill; nothing else on the mod is affected
  (the item still exists and can be granted with `@item Exp_Card`).

## Installing

Copy this folder into your mods directory and restart the app:

    macOS    ~/Library/Application Support/Ragnarok Offline/state/mods/
    Windows  %APPDATA%\Ragnarok Offline\state\mods\
    Linux    ~/.local/share/Ragnarok Offline/state/mods/

Then enable it under **Settings → Mods** (it ships off by default).

## Checking it loaded

- The supervisor prints `mods: exp-card` on start.
- The map-server log's NPC count goes up by one (`exp_card_ctrl`). A parse
  error names the file and line.
- `@extensions` in game should list `makeitem_owned` as **on** — this
  confirms the server-side gate.
- In game: `@item Exp_Card` gives you one and using it grants the exp; that
  isolates the item and the settings from the on-kill roll.

## What to look at first

`npc/exp_card.txt` is the whole mod in one screen: an `OnInit` that reads
the chance from Settings, and an `OnNPCKillEvent` that rolls it and calls
`makeitemowned`. Everything else is the item's stats (`db/item_db.yml`, with
the on-use exp calculation), its name and icon (`System/itemInfo.lua`), and
the one-line extension override (`db/extension_db.yml`).
