# prontera-vendors

Themed player vendors on Prontera's sidewalks, so a singleplayer world has a
market: cards, weapons, refined gear, potions, gemstones, dungeon loot and
more, at prices taken from a real server's player market.

Every vendor is a population-engine shell, a real `BL_PC` with a real
MC_VENDING stall, not an NPC dressed as one. Stalls come and go like players
do, and each new one draws a fresh mix from its theme.

## What it needs

- **The population engine switched on**: Settings → Population → Fake
  players, with the engine's vending economy on (`population_engine_vending_enable`,
  the default).
- An app build whose engine has mod vendors (`Spawns:`, Pool vendors, and the
  `population_vendor_*` script commands). On an older build the server log
  names the unknown keys or the unknown script command.

## Settings (Settings → Mods)

| Setting | Default | What it does |
|---|---|---|
| Sell shops | on | Off removes every sell stall. |
| Sell stalls | 20 | How many. With fewer stalls than themes, a different set of themes shows up each server start. |
| Minutes before a stall changes | 240 | How long a vendor stays before another takes the spot (± up to half, checked once a minute, so short values run long). 0 keeps them until restart. |
| Price level (%) | 100 | Every price × this / 100. Nothing goes below what an NPC pays. |
| Vendors respect the population limit | on | Off: stalls spawn even when the fake-player limit is reached (they still count in it). |
| Vendors shout their wares | on | Stalls call out a real item and price now and then. |
| Seconds between a stall's shouts | 180 | Average per stall; stalls never shout within 6 s of one another. |

Settings take effect when the server starts. They reach the engine through
`npc/prontera-vendors.txt` and `npc/prontera-vendors-newer.txt` (the second
holds the settings that need a newer app build, so an older one only loses
those). Buy shops will get their own on/off and count under
`prontera-vendors/buy/`.

## What's for sale

106 themes, one vendor key each, all on both sidewalks (x=147, y=136–170 and
x=164, y=135–173). With the default 20 stalls, each server start shows a
different random fifth of them; raise "Vendors" to see more at once.

- **Goods:** general gear, forge supplies, potions, slim potions, healing
  items, gemstones, Ygg/Ori/Elu, skill supplies, ammo, magic scrolls, dyes,
  pet and taming items, elemental converters, Undershirt + Pantie, Bloody
  Branches, OBB/OPB, OCA/MCA.
- **Cards:** common cards (monsters up to level 60) and rare cards (stronger
  monsters, mini-bosses). Never MVP cards.
- **By class:** Knight, Crusader, Wizard, Sage, Hunter, Bard/Dancer, Priest,
  Monk, Assassin, Rogue, Blacksmith, Alchemist, Taekwon/SG/SL, Ninja,
  Gunslinger, Super Novice, Doram: gear that class can wear and few others can.
- **By weapon type:** daggers, swords, two-handers, spears, axes, maces,
  staves, bows, books, knuckles, instruments and whips, guns, huuma.
- **By armor slot:** garments, footgear, shields, body armor, slotted gear,
  headgear, accessories, costumes.
- **Specials:** starter gear, low- and mid-level weapons, katars, elemental
  daggers (forged Fire/Water/Earth/Wind, some "Very Strong"), crimson
  weapons, shadow gear, a stall selling nothing but an Ice Pick, rare etc.
  collectibles, a "hunter's haul" of popular drops.
- **Refined:** weapons from their safe limit up to three past it, armor +4 to
  +7, priced by what it costs to make: the ore, and past the safe limit the
  expected cost including failures.
- **Loot:** one stall per dungeon (Byalan, Geffenia, Kiel, Payon Cave, Orc
  Dungeon, Ant Hell, Sphinx, Pyramids, Sunken Ship, Clock Tower, Glast Heim,
  Turtle Island, Toy Factory, Niflheim, Magma, Ice Cave, Abyss Lake,
  Thanatos, Odin, Juperos, Bio Lab, Comodo, Amatsu, the Culverts, the Guild
  Dungeon), loot by monster level (1–20, 21–40, 41–60, 61–80, 81–99), boss
  loot (mini-bosses) and MVP items. Loot stalls skip what dozens of
  monsters drop, so each shows its own place.
- **Random:** five stalls that each sample a broad pool at random: monster
  loot, consumables, equipment, cheap junk ("Cart Clearance") and a mixed
  bag, mostly under generic signs.

Shop signs mix theme names with the kind of vague titles real stalls use
("Stuff", "SALE", "Happy hunting!", "..."), drawn from a sample of 500 iRO
shops.

## Prices

Prices follow kRO's player market, which is cheaper and steadier than old
iRO's (Elunium ~13k rather than ~263k), and suits a solo world better:

- **kro:** the 90-day median asking price on kRO's official servers, from
  RagMAYA (ragmaya.kr), where at least 3 listings back it.
- **ragnastats:** iRO's average from ragnastats.com, converted to kRO's scale
  with a factor per kind of item (cards, weapons, loot...), learned from the
  items both sources price.
- **npc:** from the NPC price, for gear an NPC sells and items no market has.
- **sibling:** a same-named item's price (Knife -> Knife [3]).
- **estimate:** a model's ballpark from what the item is, which monsters drop
  it, how rarely, and its level and stats. Typically within ×2.7 either way;
  worth checking.

Items none of these can price stay at 0,0 in the price list and are left out
of the stalls until someone fills them in.

Each item has a `[min, max]` range, and each stall rolls inside it. Half the
time an item is listed 1–5 % under the cheapest rival stall on the map that
sells it, but never below its range. No price goes below the NPC sell value,
so nothing can be flipped to an NPC for profit, except a "fat-finger": 1 in
5000 per item, a price with a digit missing.

### Changing prices

`db/population_vendor_prices/prontera-vendors.csv` is the price list: one row
per tradeable item, `Id,Name,Min,Max,Source`, and every stall that sells the item rolls inside
that range. Open it in Excel or any editor, change what you like, and restart
the server; it wins over the prices in the YAML. The Id decides; the Name is
there to find things. A row you change is kept by the generator and marked
`manual`; the rest follow the data on each run. `;` as the separator is fine too (what Excel writes in
some locales). Refined, forged and carded lines keep the price in
`population_vendors.yml`, since a +9 isn't priced like a plain one.

The file only prices this mod's vendors (its name is the key prefix), and
needs an app build with mod price tables; older builds ignore it and use the
YAML prices.

## Behaviour

- A stall stays for the rotation time, then packs up; another takes the spot
  shortly after.
- A stall that sells out packs up too, as a player would.
- Vendors stand only on this mod's sidewalks and never count against the
  engine's own Prontera vendors, which spawn exactly as without the mod.

## Changing it

`db/population_vendors.yml` and `db/population_vendor_pop.yml` are
**generated** by `tools/build_vendors.py` from rAthena's item, monster and
spawn databases and the price caches `tools/prices_kro.json` (RagMAYA) and
`tools/prices.json` (ragnastats):

```
python3 mods/prontera-vendors/tools/build_vendors.py                   # rebuild from the cache
python3 mods/prontera-vendors/tools/build_vendors.py --refresh-prices  # fetch prices the cache lacks
python3 mods/prontera-vendors/tools/build_vendors.py --all-prices      # fetch every tradeable item (~1-2 h)
python3 mods/prontera-vendors/tools/build_vendors.py --reprice         # rebuild the CSV from market data
python3 mods/prontera-vendors/tools/scrape_ragmaya.py --workers 12     # refresh kRO prices (resumable, ~1-2 h)
```

Themes are defined at the top of the script: a hand list, a rule over the
item database, or "what these dungeons' monsters drop". The YAML can be
edited by hand for a quick test, but a re-run overwrites it.

Per vendor key in the YAML: `PickCount`, `MaxSlots`, `TitleFromPool`
(`{name}` is the vendor's name), `RotationHours`/`RotationMinutes`,
`PriceMistakeOneIn`, `Undercut`, `Callouts`, and per Pool line `Amount`,
`Price: [min, max]`, `Refine`, `Element`, `Stars`, `Cards`. `Spawns` says
where; its `Count` is the theme's share of the Vendors setting.

## Known gaps

- Pre-renewal: the pools are built from renewal data. Items a pre-renewal
  server lacks are skipped with a warning at startup, so stalls there are
  thinner.
- Names: vendors use the engine's generated names, not a list of
  player-style handles.
- Restocking in place (the same vendor with new stock) isn't done; a new
  vendor takes the spot instead.

## Files

```
mods/prontera-vendors/
├── mod.json                     settings
├── README.md
├── npc/
│   ├── prontera-vendors.txt         hands the settings to the engine
│   └── prontera-vendors-newer.txt   the ones needing a newer app build
├── db/
│   ├── population_vendors.yml       themes: pools, spawns (generated)
│   ├── population_vendor_prices/
│   │   └── prontera-vendors.csv     the price list (Id,Name,Min,Max); edit freely
│   └── population_vendor_pop.yml    one shell profile per theme (generated)
└── tools/
    ├── build_vendors.py         the generator
    ├── estimate.py              the estimate model it uses
    ├── scrape_ragmaya.py        kRO price fetcher
    ├── prices_kro.json          kRO price cache (RagMAYA)
    ├── prices.json              iRO price cache (ragnastats)
    └── table_generated.json     what the generator last wrote (to spot hand edits)
```
