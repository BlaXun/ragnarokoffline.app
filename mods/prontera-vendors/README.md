# prontera-vendors

Themed player vendors stationed on Prontera's sidewalks, rotating stock every
few hours so a singleplayer world has somewhere to buy class gear and rare
items without rolling a new character to farm for them.

Ships two Pool-type vendors, each with its own spot, pulling items from a
themed superset. Each spawn draws a random subset and picks a shop title, so a
vendor reads as a cycling market of different "players". The population engine
runs the shell as a real `BL_PC`, which means the yellow MC_VENDING banner
above its head is the authentic vending packet — not an NPC lookalike.

## What it needs

- **Population engine switched on** — Settings → Population → Fake players.
  Also the vending economy option in the engine's own section
  (`population_engine_vending_enable`), which is the default.
- A build of the app whose population engine has the `Pool` vendor type and
  mod `Spawns:`. If the server log at startup says `Type must be 'static',
  'dynamic', or 'pool'`, or warns about an unknown `Spawns` key, the engine is
  older than this mod and it cannot work until the build is updated.

## What it does today

Two vendors on the west sidewalk at `x=147`, each in its own stretch:

- **`prontera-vendors/general_gear`** (`y=136..152`, Merchant) — ~22 common
  gear and consumables, 6–10 per shell.
- **`prontera-vendors/forge_supplies`** (`y=155..170`, Whitesmith) — ores,
  elemental stones and upgrade materials, 5–8 per shell.

The engine's own vendors on Prontera spawn exactly as they would without this
mod: same jobs, same count, same places. Ours are extra. They are placed by
the mod's own `Spawns:` blocks, so they don't use up the engine's `MaxVendors`,
and no other mod's vendors are touched. They do count against the global
population Limit like any other shell.

Each vendor:

- Draws a random subset of its Pool per spawn, with hand-tuned prices.
- Rotates every 4 hours ±30 min of jitter, so vendors turn over in succession
  rather than all at once.
- Stands only where its `Spawns:` block says: exactly `Count` shells in its
  `Areas`. If the spot is taken (by a player or another shell) it waits for a
  free cell rather than standing somewhere else. `Spawns:` also takes fixed
  `Positions: [[x, y], ...]`, one shell per seat, and `ScaleWithDensity: true`
  to follow the population density slider instead of an exact count.
- Add more by appending a `VendorKey: prontera-vendors/<name>` entry here and a
  `PlacementBound: true` Profile with the same VendorKey in
  `population_vendor_pop.yml`.

## Known gaps vs the design

Agreed scope that is **not** in this MVP yet:

1. Prices are tuned to iRO Valkyrie player-market data (ragnastats.com),
   gathered by a one-off manual scrape. **Done:** per-shell price jitter
   (`PriceJitterPct`, each shell rolls each price ±%) and rare "fat-finger"
   mispricing (`PriceMistakeOneIn`, a 1-in-N dropped digit for a deal-of-a-
   lifetime find). **Caveat:** iRO is a high-zeny economy, so some values are
   steep for a solo world (Elunium ~263k). Scale the `Price` numbers down in
   the YAML if that's too rich. A scripted re-scrape and a pre-renewal price
   pass are still future work.
2. Pre-renewal price list. Right now the Pool mixes items that exist in both
   eras — items missing from an era's `item_db.yml` are warned about and
   zeroed by the engine, so the mod will still load; it will just serve a
   slightly thinner pool in pre-re.
3. More themed vendors (cards, ninja gear, pistols, armor, headgear). Two so
   far (general goods + forge supplies). Each additional theme is another
   `VendorKey:` block with its own `Spawns:` here plus a `PlacementBound: true`
   `Profile:` in `population_vendor_pop.yml`.
   - **No job limit.** `PlacementBound` resolves a vendor by its VendorKey, not
     by job, so the `Jobs:` entry is just the sprite. Any number of vendors can
     reuse the same sprite (e.g. several `Merchant`s) without colliding, and
     they never touch the engine's own vendors. Use a can-vend sprite for the
     illusion — Merchant tree (Merchant, Blacksmith, Alchemist, HighMerchant,
     Whitesmith, Creator, Mechanic, Genetic, Meister, Biolo) or Super
     Novice / HyperNovice — since only those can open a vend on a real server.
   - **Self-contained:** this mod adds only its own keys, profiles and
     spawns; it changes nothing about the engine's own vendors or other mods.
4. MVP cards / god items / event-only / non-tradable blocklist. The current
   pool is hand-authored so nothing from those categories is in it, but a
   future dynamic-pool generator will need to apply filters.
5. Authentic player-handle name pool. The shell's name comes from the
   engine's `default` NameProfile (syllable grammar / adjective-noun). A
   `pick_one` strategy with a curated handle list is a planned follow-up.
6. Settings in `mod.json`. A toggle for the rotation cadence and the max
   number of simultaneous vendors would be natural; the Pool mechanism
   already reads them from YAML, so this is a surfacing question, not an
   engine one.

## Testing it

1. Build the app so the engine's `Pool` type and `Spawns:` are compiled in
   (`scripts/apply-server-mods.sh` + the usual docker build; CI covers this
   on every push).
2. Enable this mod in Settings → Mods.
3. Make sure the population engine is on.
4. Launch the world. Within ~10s of the autosummon pass, a vendor shell
   should appear with a yellow banner and a cart somewhere along the
   west sidewalk at `x=147`.
5. Wait 4h ± 30 min with the server running: the shell should be released
   and a new one (new title, new stock subset) spawn in its place within
   a minute or two.

## Files

```
mods/prontera-vendors/
├── mod.json
├── README.md
└── db/
    ├── population_vendors.yml       Pool definition + Spawns
    └── population_vendor_pop.yml    Shell profile referencing the pool
```
