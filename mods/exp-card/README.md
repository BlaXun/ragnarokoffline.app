# exp-card

Every monster kill has a small chance to drop an **Exp Card**, bound to the
killer for the standard pickup window. Two families — **Base Exp Cards** and
**Job Exp Cards** — each with ten levels. Higher-level monsters drop
higher-level cards. Using a card grants a fixed chunk of experience.

The point: streamline the offline experience without touching per-mob drop
tables. Any mob, any map, one uniform bonus channel that scales with the
content the player is fighting.

## The cards

Exp per card follows a roughly geometric curve (~2× per level), anchored so a
Lv 10 card is about 5% of a level-98 Renewal character's next-level bar and
each lower level is roughly the same 3–5% at the player level *that band of
mobs suits* — matching the shape of rAthena's own NextBaseExp curve.

| Level | Exp | Item ids (base / job) | Typical player level |
|---|---|---|---|
| 1  | 100    | 30051 / 30061 | ~5   |
| 2  | 250    | 30052 / 30062 | ~15  |
| 3  | 500    | 30053 / 30063 | ~25  |
| 4  | 1,000  | 30054 / 30064 | ~35  |
| 5  | 2,000  | 30055 / 30065 | ~45  |
| 6  | 4,000  | 30056 / 30066 | ~55  |
| 7  | 7,500  | 30057 / 30067 | ~65  |
| 8  | 15,000 | 30058 / 30068 | ~75  |
| 9  | 30,000 | 30059 / 30069 | ~85  |
| 10 | 60,000 | 30060 / 30070 | ~95+ |

Base cards grant only base exp; Job cards grant only job exp. The two are
symmetric — a Base Lv 10 gives 60,000 base exp, a Job Lv 10 gives 60,000
job exp.

If you want a different curve, edit the twenty scripts in `db/item_db.yml`
and update the `EXP_BY_LEVEL` table in `System/itemInfo.lua` to match (so
the tooltips still show the right numbers).

## How drops work

The `exp_card_ctrl` NPC hooks `OnNPCKillEvent`, rolls one dice against the
configured chance, and — on a hit — picks *which* card:

- **Level** comes from the dead mob's `MOB_LV`, clamped to `1..10`:
  ```
  card_level = clamp((mob_level + 9) / 10, 1, 10)
  ```
  So mob levels 1–10 give a Lv 1 card, 11–20 give Lv 2, …, 91+ gives Lv 10.
- **Family** is a coin flip — 50% Base Exp Card, 50% Job Exp Card.

The card lands at the killer's position and is bound to their `char_id`
via `makeitemowned`. Nobody else can pick it up during the standard
`item_first_get_time` window (see `battle.conf`); after that, it's free.

The mob's own drop table is untouched.

## Settings

**Settings → Mods → exp-card** exposes one number, read through
`F_ModSetting` on each server start (so **Apply** takes effect on the
next restart):

- **Drop chance** (`drop_chance`, default 100 = 1%) — in 0.01% units,
  matching rAthena's drop-rate convention. 1,000 is 10%, 10,000 is
  guaranteed.

Card exp values are hard-coded in `db/item_db.yml` (twenty scripts, one
per card). Change them there if you want a different curve.

## Requirements

- `requires.app` is **`>=1.3.8`**.
- The server must have the **`makeitem_owned` extension** compiled in
  and registered — that's a rAthena fork commit (branch
  `makeitem-owned`). The mod ships `db/extension_db.yml` that enables
  it, but on a server without the extension registered, `makeitemowned`
  returns failure and the on-kill event logs a one-line error per kill;
  nothing else on the mod is affected (the items still exist and can be
  granted with `@item Base_Exp_Card_1` and friends).

## Installing

Copy this folder into your mods directory and restart the app:

    macOS    ~/Library/Application Support/Ragnarok Offline/state/mods/
    Windows  %APPDATA%\Ragnarok Offline\state\mods\
    Linux    ~/.local/share/Ragnarok Offline/state/mods/

Then enable it under **Settings → Mods** (it ships off by default).

## Checking it loaded

- The supervisor prints `mods: exp-card` on start.
- The map-server log's NPC count goes up by one (`exp_card_ctrl`). A
  parse error names the file and line.
- `@extensions` in game should list `makeitem_owned` as **on** — this
  confirms the server-side gate.
- In game: `@item Base_Exp_Card_10` gives you one, and using it grants
  60,000 base exp; that isolates the item side from the on-kill roll.

## What to look at first

`npc/exp_card.txt` is the whole feature in one screen: an `OnInit` that
reads the chance from Settings, and an `OnNPCKillEvent` that rolls it,
picks a card level from `MOB_LV`, flips for family, and calls
`makeitemowned`. Everything else is item entries (`db/item_db.yml`,
twenty scripts), their client-side names built with a small loop
(`System/itemInfo.lua`), and the one-line extension override
(`db/extension_db.yml`).
