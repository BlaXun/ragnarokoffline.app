# steal-cards

The Thief's `Steal` skill can return cards.

**1,260 monsters** — every non-MVP monster in rAthena's `mob_db.yml` that has
a card drop — gain a stealable card slot. Killing them still rolls the card
drop at its stock rate; Steal now rolls it too.

MVPs are excluded, so Baphomet's card stays untouchable — and so do
Doppelganger, Dracula, Phreeoni, Eddga, Orc Hero, Moonlight Flower and the
other 190-odd. Mini-bosses like Angeling, Deviling, Ghostring and Vagabond
Wolf are `Class: Boss` but not real MVPs (they have no `MvpDrops:` and no
`Modes.Mvp: true`), so their cards *are* stealable, which is usually the whole
reason a Thief learns Steal in the first place.

## Why the skill ignores cards to begin with

`Steal` (`TF_STEAL`) is `pc_steal_item` in `vendor/rathena/src/map/pc.cpp`. It
walks the target monster's `Drops[]` table, filters out every entry marked
`steal_protected`, and picks one of the rest by weight. rAthena's stock
`db/re/mob_db.yml` and `db/pre-re/mob_db.yml` both mark **every card drop as
`StealProtected: true`**, so the eligible list is always Jellopy and Sticky
Mucus and never the card. The C code does the right thing; the data locks the
door.

That means the fix belongs in `db/`, not on the fork.

## What this mod does

`db/mob_db.yml` here is 1,260 entries of exactly this shape:

```yaml
- Id: 1002 # Poring (PORING) -- Poring_Card
  Drops:
    - Index: 7
      StealProtected: false
```

`db/import` layers over rAthena's own table — see
[docs/MODDING.md](../../../docs/MODDING.md) — and only the fields spelled here
are touched. Poring's Jellopy, Knife, Sticky Mucus and the rest of its stock
drops are exactly where they were, at the rates they were. All this file
changes is the one flag on Slot 7.

**The `Index:` matches the card's real slot in the stock table** — 7 for
Poring, 6 for Ghostring, 8 for many second-job monsters. The generator reads
`vendor/rathena/db/re/mob_db.yml` and copies the index verbatim, so the
override lands on the same drop the on-kill roll uses. Nothing is duplicated
and nothing else moves.

`Item:` and `Rate:` are deliberately **not** restated. rAthena's
`MobDatabase::parseDropNode` treats them as optional on an override that
targets an existing `Index:`, so the card name and its stock drop rate are
whatever rAthena ships them as. That matters when the vendor pin moves and
rAthena bumps a rate: the on-kill roll and the Steal roll track the new
value automatically. Spell `Rate:` on an override only when you want to
pin a specific card's drop weight — note it affects both the on-kill roll
and Steal, since both pull from the same `Drops[]` entry.

`pc_steal_item` weights each eligible drop by its own rate (multiplied by the
skill's dexterity/luck term and its skill-level base rate), so a 0.01% card
is much rarer than the mob's junk drops, but rarely more than a few casts per
stealing session on the lower-tier mobs.

### Why the override is this small

Until rAthena [Flux159/rathena#4](https://github.com/Flux159/rathena/pull/4),
`MobDatabase::parseDropNode` required `Item` and `Rate` on every drop entry
and rewrote every field on the target slot. An override wanting to touch only
`StealProtected` had to restate the stock `Item` and `Rate`, and would silently
drift the moment rAthena bumped the on-kill rate underneath it. With that fix
in place, an override spells only the fields it changes, and the rest of the
drop is left alone.

## Confirming it works

Install the folder, restart the server (Settings → Restart server, since only
`db/` changed — no app restart needed), and:

1. Look at the map server log for `Loading '1260' entries in
   'db/import/mob_db.yml'`. Fewer entries means part of the file didn't parse.
2. Roll a Thief, learn Steal, find a Poring. `@whodrops 4001` (Poring Card)
   lists Poring at its rate.
3. Cast Steal on Porings until one gives up the card. At Poring's stock
   `Rate: 20` (0.2%) and the skill's own dexterity term, plan on fifty to
   two hundred casts on a fresh Thief; a higher-level one with Luk gear
   gets there faster.

If Steal still only returns Jellopy and Apple, check the log for a YAML parse
error and check that the target monster's Id is in `db/mob_db.yml`.

## Regenerating the table

`generate.py` reads rAthena's own `mob_db.yml` and rewrites `db/mob_db.yml`.
Run it when the vendor pin moves, or when you want to change the criteria.

```sh
# beside a checked-out vendor tree
./generate.py ../../../vendor/rathena/db/re/mob_db.yml

# or against a copy elsewhere
./generate.py ~/rathena/db/re/mob_db.yml --out db/mob_db.yml
```

PyYAML is the only requirement: `pip install pyyaml`. The generator writes to
`db/mob_db.yml` next to itself by default.

**Renewal versus pre-renewal.** rAthena ships two mob tables that differ in
level, HP, damage and a handful of drops — `db/re/mob_db.yml` and
`db/pre-re/mob_db.yml`. The supervisor mounts whichever era the app is running
in, and `db/import` layers over that one. Both tables agree on the *card*
slot for the mobs both include, so generating from either produces the same
override for the mobs it covers; renewal adds ~200 monsters that pre-renewal
does not have, and those entries are simply unused in pre-renewal. Generating
from `db/re/mob_db.yml` is the wider choice.

### What the generator excludes

`is_mvp()` in `generate.py`. Two rules:

1. `MvpDrops:` field present — Baphomet, Turtle General, Ktullanux, the whole
   real-MVP list.
2. `Modes.Mvp: true` — a handful of MVPs (Bone Detale, EP18_MD_SCHULANG) that
   set the mode without an explicit MvpDrops block.

**`Class: Boss` is not enough.** 539 monsters carry `Class: Boss` without
being MVPs: mini-bosses, boss-class field monsters, event bosses. Their cards
stay in the mod. If you want a stricter version — no bosses at all, however
minor — add `if mob.get("Class") == "Boss": return True` at the top of
`is_mvp()` and rerun.

## What this mod is not

- **It does not change what `Steal` costs, how far it reaches, or its
  formula.** That is `db/skill_db.yml` and `TF_STEAL` in `src/map/skill.cpp`,
  and both are left alone. The rate `pc_steal_item` weights by is the mob's
  own stock drop rate (unchanged by this mod) — the skill's base success rate
  applies on top.
- **It does not make MVP cards stealable.** They are excluded by design. If
  you want them in too, edit `is_mvp()` in `generate.py` to `return False` and
  rerun.
- **It does not touch drops that are not cards.** Card equipment drops
  (Poring Hat, etc.) stay steal-protected if they were, and stealable if they
  were. Only slots whose item name ends in `_Card` are rewritten.
- **It does not remove the client's own "cards cannot be stolen" cooldown
  string.** rAthena stopped sending that message the moment the eligible list
  contained a card, so it never appears with this mod installed. The client
  literal in `msgstringtable.txt` is left alone.

## Applying it

`db/` is read when the server starts. Settings → Restart server is enough.
