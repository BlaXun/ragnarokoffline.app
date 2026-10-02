# prontera-vendors

Themed player vendors stationed on Prontera's sidewalks, rotating stock every
few hours so a singleplayer world has somewhere to buy class gear and rare
items without rolling a new character to farm for them.

Ships two Pool-type vendors, each pinned to its own spot, pulling items from a
themed superset. Each spawn draws a random subset and picks a shop title, so a
vendor reads as a cycling market of different "players". The population engine
runs the shell as a real `BL_PC`, which means the yellow MC_VENDING banner
above its head is the authentic vending packet — not an NPC lookalike.

## What it needs

- **Population engine switched on** — Settings → Population → Fake players.
  Also the vending economy option in the engine's own section
  (`population_engine_vending_enable`), which is the default.
- A build of the app with the `Pool` vendor type in the population engine. If
  the server log at startup says `Type must be 'static', 'dynamic', or 'pool'`
  for this mod's vendor, the engine is older than the Pool addition and the
  mod cannot work until the build is updated.

## What it does today

Two vendors on the west sidewalk at `x=147`, each pinned to its own spot:

- **`pv_general_gear`** (`y=136..152`, Merchant) — ~22 common gear and
  consumables, 6–10 per shell.
- **`pv_forge_supplies`** (`y=155..170`, Whitesmith) — ores, elemental stones
  and upgrade materials, 5–8 per shell.

The engine's own generic vendors (`field_drops`, `dungeon_drops`) still run
alongside these — they're wanted as plain "player selling their loot" stalls.
Our two just take one job each from them (Merchant, Whitesmith); the generics
keep their other job (HighMerchant, Blacksmith) and still spawn.

Each vendor:

- Draws a random subset of its Pool per spawn, with hand-tuned prices.
- Rotates every 4 hours ±30 min of jitter, so vendors turn over in succession
  rather than all at once.
- Is bound to its own `VendorPlacement` by VendorKey, so the two never get
  swapped and each stays at its spot. Add more by appending a VendorKey entry
  here plus a matching Profile (on a distinct job) in
  `population_vendor_pop.yml`.

## Known gaps vs the design

Agreed scope that is **not** in this MVP yet:

1. Prices from a real market. Values here are rough placeholders in the
   "what a player would charge" direction. The intended source is
   [ragnastats.com](https://ragnastats.com/) (iRO Valkyrie market data). The
   scraper has not been written yet.
   - Per-shell price jitter is also planned: each vendor should roll its own
     price around the base (vendors undercutting each other, like a real
     market) instead of every shell showing the same number. Deferred.
   - "Fat-finger" mispricing (planned): on real servers humans set prices by
     hand and occasionally drop a digit, so a rare item is listed far too
     cheap. A VERY low chance (e.g. well under 1% per item) of an item's price
     being divided by ~10 would recreate the deal-of-a-lifetime moment and sell
     the illusion of human vendors. Deferred.
2. Pre-renewal price list. Right now the Pool mixes items that exist in both
   eras — items missing from an era's `item_db.yml` are warned about and
   zeroed by the engine, so the mod will still load; it will just serve a
   slightly thinner pool in pre-re.
3. More themed vendors (cards, ninja gear, pistols, armor, headgear). Two so
   far (general goods + forge supplies). Each additional theme is another
   `VendorKey:` block here plus a `Profile:` on a distinct job in
   `population_vendor_pop.yml`. Multiple placements per map now work, so each
   can have its own spot.
   - **Job budget:** only the Merchant tree + Super Novice can actually vend,
     and each vendor needs its own job (the job → VendorKey map is global,
     last-wins). Vending-capable jobs: Merchant, Blacksmith, Alchemist,
     HighMerchant, Whitesmith, Creator, Mechanic, Genetic, Meister, Biolo,
     SuperNovice, HyperNovice (12). The engine's generics use 4
     (Merchant/HighMerchant/Blacksmith/Whitesmith) and we share two of those,
     leaving ~8 free jobs → ~8 more themed vendors before the model runs out.
   - **Past that ceiling** we'd want an engine change letting a
     `VendorPlacement` name its `VendorKey` directly (and the engine pick a job
     from that vendor's Profile), removing the one-job-per-vendor limit. Planned
     if the themed set grows large.
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

1. Build the app so the engine's `Pool` vendor type is compiled in
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
    ├── population_vendors.yml       Pool definition + placement
    └── population_vendor_pop.yml    Shell profile referencing the pool
```
