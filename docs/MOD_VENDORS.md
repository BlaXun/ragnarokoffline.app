# Mod vendors

A mod can put its own fake-player vendors in the world: vending stalls and
buying stores that stand where the mod says, sell or buy what the mod says,
at the prices the mod says, and come and go like players do. They are
population-engine shells — real characters with a real MC_VENDING stall or
buying store — so a player trades with them exactly as with anyone else.

This page is the reference. The worked example is
[`registry/mods/prontera-vendors`](../registry/mods/prontera-vendors/), which
fills Prontera's main road with 115 kinds of sell stall and 15 kinds of buyer
from two markets.

**Nothing here changes a world that doesn't use it.** The engine's own
vendors keep their own placement, counts and stock; mod vendors are spawned
by a pass of their own, after the engine's, and never use up its numbers.

- [What you need](#what-you-need)
- [The pieces](#the-pieces)
- [A minimal mod](#a-minimal-mod)
- [population_vendors.yml](#population_vendorsyml): [vendors](#vendor-entries), [stock](#pool-lines), [Spawns](#spawns), [markets](#markets), [buying stores](#buying-stores)
- [population_vendor_pop.yml](#population_vendor_popyml): the shells
- [The price table](#the-price-table)
- [Settings from mod.json](#settings-from-modjson)
- [Chat](#chat)
- [How a vendor lives](#how-a-vendor-lives)
- [How a price is made](#how-a-price-is-made)
- [Ownership: playing well with other mods](#ownership-playing-well-with-other-mods)
- [Tools: @vendorinfo and the server log](#tools-vendorinfo-and-the-server-log)
- [Limits](#limits)
- [Troubleshooting](#troubleshooting)

## What you need

- **App 1.4.5 or later.** Markets, buying stores, the price table, the
  `population_vendor_*` script commands and `@vendorinfo` arrived together.
  Put `"requires": { "app": ">=1.4.5" }` in your `mod.json`.
- **The population engine switched on** in the player's world (Settings →
  Population → Fake players), with `population_engine_vending_enable` on,
  which is the default. Without it no shell appears; nothing fails.

## The pieces

```
my-mod/
├── mod.json
├── db/
│   ├── population_vendors.yml        what is sold or bought, and where (required)
│   ├── population_vendor_pop.yml     what each vendor looks like (required)
│   └── population_vendor_prices/
│       └── my-mod.csv                a price list (optional)
└── npc/
    └── my-mod-settings.txt           hands mod.json settings to the engine (optional)
```

Both YAML files are ordinary rAthena tables that the engine imports from
`db/import/`; the app merges every mod's copy entry by entry, so several mods
can each add vendors. **Every key you define starts with your mod's name and a
slash** (`my-mod/potions`): see [Ownership](#ownership-playing-well-with-other-mods).

A vendor is two entries with the same key:

| File | Entry | Says |
|---|---|---|
| `population_vendors.yml` | `VendorKey: my-mod/potions` | the stock, prices, signs, rotation — and, with `Spawns:`, where it stands |
| `population_vendor_pop.yml` | `Profile:` with `VendorKey: my-mod/potions` and `PlacementBound: true` | the shell: job sprite, hair, gear, name |

## A minimal mod

One potion seller on a fixed spot in Prontera, one buyer of Jellopy beside it.

`db/population_vendors.yml`:

```yaml
Header:
  Type: POPULATION_VENDORS_DB
  Version: 1

Body:
  - VendorKey: my-mod/potions
    Type: Pool
    TitleFromPool: ["S> pots", "{name}'s Pharmacy", "potions cheap"]
    PickCount: [3, 5]
    RotationHours: 4
    RotationJitterMinutes: 30
    Pool:
      - { Item: Red_Potion,    Amount: 200, Price: [8, 12] }
      - { Item: Orange_Potion, Amount: 100, Price: [45, 60] }
      - { Item: White_Potion,  Amount: 50,  Price: [300, 420] }
      - { Item: Blue_Potion,   Amount: 20,  Price: [1600, 2000] }
      - { Item: Wing_Of_Fly,   Amount: 100, Price: [170, 230] }
    Spawns:
      - Map: prontera
        Positions:
          - [150, 160]

  - VendorKey: my-mod/jellopy_buyer
    Type: Pool
    Buying: true
    TitleFromPool: ["B> jellopy", "buying jellopy"]
    Pool:
      - { Item: Jellopy, Amount: 300, Price: [4, 6] }
    Spawns:
      - Map: prontera
        Positions:
          - [152, 160]
```

`db/population_vendor_pop.yml`:

```yaml
Header:
  Type: POPULATION_ENGINE_DB
  Version: 2

Body:
  - Profile: my-mod/potions_vendor
    PlacementBound: true
    Jobs:
      Alchemist: para_merchant
    NameProfile: default
    Flags: [mortal]
    TownBehavior: vendor
    VendorKey: my-mod/potions
    Script: |
      setcart;

  - Profile: my-mod/jellopy_buyer_vendor
    PlacementBound: true
    Jobs:
      Knight: para_knight_base
    NameProfile: default
    Flags: [mortal]
    TownBehavior: vendor
    VendorKey: my-mod/jellopy_buyer
```

That is a working mod. Everything below is about doing more with it.

## population_vendors.yml

`Header: Type: POPULATION_VENDORS_DB, Version: 1`. Its `Body` holds two kinds
of entry: **vendors** (`VendorKey:`) and **markets** (`Market:`).

### Vendor entries

| Field | | |
|---|---|---|
| `VendorKey` | required | `my-mod/<name>`. Matches the profile's `VendorKey`. |
| `Type` | `Pool` | `Pool` for mod vendors: each stall draws a random set from `Pool`. (`Static` sells `Stock:` as listed; `Dynamic` derives stock from monster drops — the engine's own vendors use those.) |
| `Title` | | a fixed shop sign, used when there is no `TitleFromPool` |
| `TitleFromPool` | | signs to pick from. `{name}` becomes the shell's name ("{name}'s Shop"). Two stalls on one map never show the same sign: another from the pool is taken, or a number is added ("potions cheap 2"). |
| `PickCount` | `[min, max]` | how many different items a stall lists, rolled per stall. 1–12. |
| `MaxSlots` | 12 | hard cap on listed items (MC_VENDING 10 allows 12). |
| `Pool` | | the items to draw from: see [Pool lines](#pool-lines) |
| `RotationHours` / `RotationMinutes` | 0 | how long a stall stays before packing up; a new one then takes the spot. 0 = until the server restarts. Minutes win over hours. |
| `RotationJitterMinutes` | 0 | each stall's lifetime varies by up to this either way (capped at half the rotation), so a street doesn't turn over at once |
| `PriceJitterPct` | 0 | for a line with a single `Price`: each stall rolls it within ±this % (0–90) |
| `PriceMistakeOneIn` | 0 | "fat-finger": 1-in-N per listed item of a price with a digit missing. Thousands keeps it a rare find. |
| `Undercut` | | `{ Chance: 50, StepPct: [1, 5] }`: each plain item has Chance % to be listed StepPct % under the cheapest rival shell stall on the map selling it |
| `Callouts` | | `{ EverySeconds: [90, 270], MapGapSeconds: 6 }`: see [Chat](#chat) |
| `Buying` | false | a buying store instead of a stall: see [Buying stores](#buying-stores) |
| `Spawns` | | where its shells stand: see [Spawns](#spawns). A vendor used only as a market's theme has none. |

`VendorPlacement:` also exists. It is the engine's own per-map placement — one
per map, last one read wins — so **a mod should not use it**; it would replace
the engine's Prontera placement for everyone. Use `Spawns:` or a market.

### Pool lines

```yaml
- { Item: Elunium, Amount: 20, Price: [12000, 14000] }
- { Item: Stiletto, Amount: 1, Price: [180000, 220000], Refine: 7 }
- { Item: Stiletto, Amount: 1, Price: [80000, 95000], Element: Fire, Stars: 1 }
- { Item: Guard_, Amount: 1, Price: [150000, 180000], Cards: [Thara_Frog_Card] }
```

| Field | |
|---|---|
| `Item` | Aegis name or item id |
| `Amount` | how many the stall holds (a buyer: how many it wants, see below). Equipment, cards, pet eggs and pet gear don't stack: use 1. |
| `Price` | `[min, max]`: each stall rolls in the range. A single number is a fixed price (with `PriceJitterPct`, ±%). 0 = the item's NPC buy price. |
| `Refine` | a refine level, or `[min, max]` rolled per stall. Equipment that can be refined only. |
| `Element` | `Water`/`Ice`, `Earth`, `Fire`, `Wind`: a forged weapon, signed by the shell ("Galaper's Fire Stiletto"). Weapons only. |
| `Stars` | 1–3 Star Crumbs on a forged weapon (3 = "Very Strong") |
| `Cards` | cards in its slots, up to the item's slot count; not with `Element`/`Stars` |

A stall draws `PickCount` of these at random. A pool larger than `PickCount`
is what makes each stall different from the last. Two lines may name the same
item with different refines or cards; they are separate listings.

### Spawns

Where a vendor's (or a market's) shells stand. A list; each block is one of
two shapes.

**Fixed seats** — one shell per position:

```yaml
Spawns:
  - Map: prontera
    Positions:
      - [150, 160]
      - [150, 164]
```

A seat someone is standing on (a player, another shell) stays empty until it
is free; the vendor never stands somewhere else instead.

**A count in areas** — that many shells anywhere inside:

```yaml
Spawns:
  - Map: prontera
    Count: 4
    Areas:
      - { X1: 147, Y1: 136, X2: 147, Y2: 170 }
      - { X1: 164, Y1: 135, X2: 164, Y2: 173 }
    MinSpacing: 2
```

| Field | |
|---|---|
| `Map` | map name |
| `Positions` | `[x, y]` seats, or |
| `Count` + `Areas` | how many, and the rectangles they may stand in (`Area:` for just one). Larger areas get proportionally more shells. |
| `MinSpacing` | cells kept between this block's own shells |
| `ScaleWithDensity` | `true` to follow the player's population density slider; counts are exact otherwise |

Cells must be walkable and allow vending and buying stores. Shells spawn up
to the count, a few per tick, while the map is live: with the engine's
on-demand spawning (the default) that is while a player is on it and a short
grace after the last one leaves; without it, always.

### Markets

A market is a set of spots and a weighted list of vendors — *themes* — that
may stand on them. Each time a spot gets a stall (at the start, after a
rotation, after a sell-out) it rolls a theme, so over a session the whole
range passes through. This is how `prontera-vendors` fits 115 kinds of stall
into 20 spots.

```yaml
- Market: my-mod/street
  Spawns:
    - Map: prontera
      Count: 20
      Areas:
        - { X1: 147, Y1: 136, X2: 147, Y2: 170 }
  Themes:
    - { Theme: my-mod/potions, Weight: 3, Min: 1, Max: 2 }
    - { Theme: my-mod/cards,   Weight: 2, Max: 1 }
    - { Theme: my-mod/ice_pick, Weight: 1, Max: 1 }
```

| Field | |
|---|---|
| `Market` | `my-mod/<name>` |
| `Spawns` | as above; its `Count` is the number of spots |
| `Themes` | vendor keys (entries **without** their own `Spawns`) with `Weight` (relative chance, default 1), `Min` (spots always kept on it, default 0) and `Max` (most at once, 0 = no limit) |

The roll: any theme below its `Min` first; otherwise a weighted pick where a
theme's weight is divided by one plus the stalls of it already standing (so
the street stays varied), skipping themes at their `Max`. Each theme still
needs its own `PlacementBound` profile. A theme's stall counts as one of the
market's spots, but sells, signs, rotates and shouts as the theme says.

Sell stalls and buyers can share a market, but two markets (one each) are
easier to size from settings.

### Buying stores

`Buying: true` turns a vendor into a player-style buying store: players right
click it and **sell to it**.

```yaml
- VendorKey: my-mod/ore_buyer
  Type: Pool
  Buying: true
  TitleFromPool: ["B> ori elu", "buying ores"]
  PickCount: [2, 4]
  Pool:
    - { Item: Oridecon, Amount: 30, Price: [7500, 10500] }
    - { Item: Elunium,  Amount: 50, Price: [7200, 10000] }
    - { Item: Steel,    Amount: 30, Price: [3100, 4400] }
```

- **Up to 5 items** at once (rAthena's buying store limit); `PickCount` above
  5 is cut to 5.
- **Only items flagged `BuyingStore`** in rAthena's item database — loot,
  materials, cards, consumables; never equipment. Others are skipped.
- `Amount` is the most it wants; each store asks for between half and all of
  it. `Price` is what it pays, rolled per store, never less than an NPC would
  pay (or the player would just sell there).
- The shell is given exactly the zeny it offers and room to carry it all.
- When it has bought everything or spent its zeny, rAthena closes the store
  and the shell packs up like a sold-out stall; buyers rotate like sellers.
- Anyone can open a buying store, so a buyer's profile may use any job.

### Pet eggs

A pet egg only hatches with a pet record behind it, and a stall's eggs have
none. When a player buys an egg from a shell, the server creates a real egg
for them at that moment (and nothing for eggs nobody buys). So sell eggs like
any item — `Amount: 1` per line, eggs listed in rAthena's `pet_db`.

## population_vendor_pop.yml

`Header: Type: POPULATION_ENGINE_DB, Version: 2`. One profile per vendor (and
per market theme):

```yaml
- Profile: my-mod/potions_vendor
  PlacementBound: true
  Jobs:
    Alchemist: para_merchant
  NameProfile: default
  Hair: [0, 42]
  HairColor: [0, 131]
  ClothesColor: [0, 699]
  Flags: [mortal]
  TownBehavior: vendor
  VendorKey: my-mod/potions
  Script: |
    setcart;
```

| Field | |
|---|---|
| `PlacementBound: true` | required for mod vendors: the profile is found by its `VendorKey`, not by job, so several vendors can share a job and none of them displaces the engine's own vendor of that job |
| `Jobs` | one `Job: GearSet` pair — the sprite and its gear. Use a job that can vend for a stall (Merchant line, Super Novice); a buyer can be any job. Gear sets come from the engine's `population_gear_sets.yml` (`para_merchant`, `para_knight_base`, `para_mage`, `para_bow`, `para_monk`, `para_thief`, `para_crusader`, `low_blunt`, …). |
| `TownBehavior: vendor` | required: the shell sits and opens its stall or store |
| `VendorKey` | the vendor it runs |
| `NameProfile`, `Hair`, `HairColor`, `ClothesColor`, `Flags`, `Script` | as for any engine profile; `setcart;` gives a stall a cart |

## The price table

`db/population_vendor_prices/<prefix>.csv` prices **plain** pool lines of the
vendors whose key starts with `<prefix>/` — the file name is the prefix, so
`my-mod.csv` covers `my-mod/*` and nothing else.

```csv
# my-mod prices
Id,Name,Min,Max,Source
985,Elunium,12000,14000,kro
501,Red Potion,8,12,manual
7135,Fire Bottle,0,0,
```

- One row per item; **Id decides**, Name is for people (and is looked up only
  when Id is empty). `Max` may be left out. Extra columns are ignored.
- A row wins over the YAML `Price` of every plain line of that item, in every
  matching vendor — sellers and buyers. Lines with `Refine`, `Element`,
  `Stars` or `Cards` keep their YAML price.
- `Min` 0 (or empty) means "no price yet": the row is skipped and the YAML
  price stands, so a table can list every item and be filled in over time.
- Quoted fields work, and `;` as the separator too (what Excel writes in some
  locales). Lines starting with `#` are comments.
- Read when the server starts and on `@reloadpopenginedb`. The log says
  `price table '…': N items, M stall lines priced`.

It is the friendliest place for a player to tune a mod's economy: open it in
a spreadsheet, sort, edit, restart.

## Settings from mod.json

A mod's settings reach scripts (through `F_ModSetting`), and these script
commands hand them to the engine. Call them from an `OnInit` in your mod's
`npc/`. Each applies to the vendors whose key starts with the prefix; the
longest matching prefix wins.

| Command | |
|---|---|
| `population_vendor_count "<prefix>", <n>;` | the total shells for those vendors and markets, split across their Spawns blocks by their YAML counts (a market's spots). A negative number goes back to the YAML. 0 removes them. |
| `population_vendor_rotation "<prefix>", <minutes>;` | rotation in minutes (0 = never) |
| `population_vendor_callouts "<prefix>", <on>{, <min s>{, <max s>}};` | callouts on/off and each stall's wait between them |
| `population_vendor_limit "<prefix>", <respect>;` | 1 (default): wait for room under the world's fake-player limit. 0: spawn anyway (they still count toward it). |
| `population_vendor_price "<prefix>", <percent>;` | price level: every price × percent / 100 (NPC floor still applies) |

```
-	script	MyModVendorSettings	-1,{
	end;
OnInit:
	.@mod$ = "my-mod";
	population_vendor_count "my-mod/", callfunc("F_ModSetting", .@mod$, "stalls", 20);
	population_vendor_rotation "my-mod/", callfunc("F_ModSetting", .@mod$, "rotation_minutes", 240);
	population_vendor_price "my-mod/", callfunc("F_ModSetting", .@mod$, "price_pct", 100);
	end;
}
```

Settings take effect when the server starts. Mod settings are whole numbers
in scripts, which is why the price level is a percentage. A count lowered
below what stands releases the extra shells; the totals are split by
largest remainder, ties broken by a seed drawn at each start, so with fewer
spots than blocks a different set appears each time.

## Chat

Vendor shells call out in public chat now and then. Lines come from the
engine's `population_chat.yml`: the `vendor_call` category for stalls,
`buyer_call` for buying stores (a buyer with no `buyer_call` lines stays
quiet). Placeholders:

| | |
|---|---|
| `{item}`, `{price}` | a real item from the stall (or what a buyer buys) and its price, compacted ("13K", "1.5M"). A line using them is skipped for a shell with nothing listed. |
| `{name}`, `{map}`, `{job}` | the shell's name, map and job |

`Callouts: { EverySeconds: [min, max], MapGapSeconds: n }` on a vendor sets
each stall's wait between lines (its first line lands anywhere in that range,
so a street that spawns at once doesn't open in chorus) and keeps any two
vendor lines on the map at least `n` seconds apart. Without it the engine's
global chat cooldown applies. `population_vendor_callouts` overrides both.

## How a vendor lives

1. **Spawn.** On the engine's autosummon tick, for every live map (see
   [Spawns](#spawns)), the mod
   pass fills each Spawns block (or market) up to its count: a free cell, a
   shell from the profile, a stall or store from the vendor (or a theme rolled
   from the market). A few per tick; it respects the world's fake-player
   limit unless the mod says otherwise.
2. **Trade.** Players buy from the stall or sell to the store like any other.
3. **Leave.** A once-a-minute sweep releases a shell whose stall sold out,
   whose store closed (all bought, or out of zeny), or whose rotation time
   has passed. Sold-out stalls go first; rotations are taken up to 8 per
   sweep.
4. **Refill.** The next spawn pass puts a new shell — new name, new stock,
   new sign, and for a market a new roll of theme — on the spot.

A server restart starts everything fresh.

## How a price is made

For each line a stall lists:

1. **Base:** the price table row if there is one; otherwise the line's
   `Price` range (rolled) or single price (± `PriceJitterPct`).
2. **Price level:** × the mod's `population_vendor_price` percent.
3. **Undercut:** with `Undercut`, Chance % of the time, StepPct % under the
   cheapest rival shell stall on the map selling the same plain item
   (ignoring rivals' fat-finger listings).
4. **Round** to what a player would type (500s above 10k, 50s above 1k, 5s
   above 100).
5. **Floors:** never below the line's own range, and never at or below the
   item's NPC sell price — nothing can be flipped to an NPC for profit.
6. **Fat-finger:** 1 in `PriceMistakeOneIn`, the price loses a digit — the one
   price allowed under the floor.

A buyer's price is its line's range at the price level, rounded, and never
below the NPC sell price.

## Ownership: playing well with other mods

Every mod's vendor tables are merged into one, so keys are what keep mods
apart:

- **Prefix every key** — `VendorKey`, `Market`, `Profile` — with
  `<mod-name>/`. Your settings commands and price table then reach only yours.
- **Never `Clear: true`** in these tables: it empties the engine's vendors and
  every other mod's.
- **Don't use `VendorPlacement`**: it is the engine's one-per-map placement.

The app checks and reports, under your mod in Settings → Mods (never by
refusing to load it): a mod vendor or market key without your prefix, a key
another enabled mod also defines (the later one wins), and `Clear: true`.
Overriding one of the engine's own vendor keys the way upstream does is not
reported unless two mods do it.

## Tools: @vendorinfo and the server log

- `@vendorinfo` — every mod stall and store on your map: owner, position,
  vendor key, sign, item count, minutes to rotation.
- `@vendorinfo <key>` — a vendor's settings and full pool with price ranges,
  or a market's themes with weights and how many of each stand now. The last
  part of a key is enough (`@vendorinfo sidewalks`).

At startup the log shows each settings command as it lands
(`mod vendors 'my-mod/*': 20 in total`), the price table line, and warnings
for anything that didn't parse: an unknown item, a theme without a profile,
a market without themes.

## Limits

| | |
|---|---|
| Items per stall | 12 (`PickCount`, `MaxSlots`) |
| Items per buying store | 5 |
| Buying store price | 1 – 99,990,000 per item |
| Price | up to the server's max zeny |
| Refine | 0 – 20 (equipment that can be refined) |
| Rotation | up to a week; jitter up to 3 hours |
| `PriceJitterPct` | 0 – 90 |

## Pre-renewal

Items differ between eras. A mod can ship a second set for pre-renewal
servers with `"prerenewalFolder": "pre-re"` in `mod.json` and the same layout
under `pre-re/db/` (and `"renewalFolder"` the other way round); files there
replace those of the same name. `prontera-vendors` builds both from rAthena's
tables with its generator in `registry/tools/prontera-vendors/`.

## Troubleshooting

| Symptom | Look at |
|---|---|
| No stall at all | Population engine on? App ≥ 1.4.5? Someone on the map? Server log for "no PlacementBound profile" or parse warnings. `@vendorinfo` on the map. |
| Fewer stalls than the count | The world's fake-player limit (try `population_vendor_limit … 0`), occupied seats, cells that don't allow vending, or the per-tick spawn budget (give it a few seconds). |
| A stall with no items | Every pool line failed: unknown item names, items that can't go in a cart, or an empty pool. |
| A buyer never opens | No pool item has the `BuyingStore` flag, or the shell couldn't hold them; the log says "could not open its buying store". |
| Prices ignore the CSV | The file name must be the key prefix (`my-mod.csv` for `my-mod/…`); the row must have `Min` > 0; refined/forged/carded lines keep YAML prices. |
| Settings don't apply | The settings script must load (check the log for script errors) and run `OnInit`; prefixes must match your keys. |
