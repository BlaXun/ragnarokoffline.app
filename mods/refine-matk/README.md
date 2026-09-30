# refine-matk

Weapon refining also grants MATK, so a blacksmith is worth visiting as a
magic-damage class.

**It ships switched off.** Settings → Mods → tick it → Apply, then relog.

## The problem it fixes

In rAthena, refining a weapon only touches its ATK. The refine table
(`db/(pre-)re/refine.yml`) has fields for a flat weapon-ATK bonus, a random
extra spread and blacksmith blessing counts — none for MATK. The status
recalculator in `src/map/status.cpp` reads those and writes them into the
weapon's ATK slots (`wa->atk2`, `wa->atk` for the random spread) and never
into `wa->matk`.

The visible result: a Wizard's +10 staff and their +0 staff are worth exactly
the same MATK. Everything a blacksmith does for a swordsman does nothing at
all for a caster.

## What it grants

While the mod is on and the player has a weapon equipped on the main hand,
they get a flat MATK bonus of:

    MATK = (main-hand refine level) × (matk_per_refine)

`matk_per_refine` is one setting under **Settings → Mods → refine-matk**,
default `2`, range `0..50`. So the ordinary case:

| weapon             | refine | setting | MATK bonus |
|--------------------|--------|---------|------------|
| Rod                | +7     | 2       | +14        |
| Staff              | +10    | 2       | +20        |
| Wizardry Staff     | +15    | 2       | +30        |
| Survivor's Rod     | +10    | 3       | +30        |
| any weapon         | +0     | any     | 0          |

The setting takes effect on the next **Apply** (server restart). Set it to
`0` to switch the bonus off without disabling the mod — useful if you want
to keep the mod ticked while you A/B-test something else.

Weapon *tier* (Lv1..Lv4) is not part of the formula on purpose: one knob is
easier to reason about than four, and the numbers a server owner picks
here are almost always going to be the same across tiers. If you want
tier-scaled bonuses instead, edit `.@per` in `npc/refine_matk.txt` to look
up a per-tier value.

## What it does not touch

- **Off-hand items.** Only `EQI_HAND_R` (main-hand) counts. Dual-wielding two
  weapons still only scores the main-hand's refine — matching how the base
  game already treats stat gear.
- **Armor refining.** Only weapons.
- **The refine.yml table.** rAthena's refine data is left alone, so ATK
  bonuses from refining are exactly as upstream ships them. This mod adds
  MATK on top; it does not rebalance ATK.
- **Cards, enchants and item scripts.** Any `bonus bMatk` already on your
  weapon still applies; this mod stacks with them, it does not replace them.

## How it works

There is no data field in rAthena to declare "MATK per refine", so the mod is
one NPC script (`npc/refine_matk.txt`) with three moving parts:

1. **`OnPCLoginEvent`** starts a per-player refresh loop as soon as the
   character connects.
2. **The loop** reads `getequipid(EQI_HAND_R)`, `getequiprefinerycnt(EQI_HAND_R)`
   and the weapon's `ITEMINFO_WEAPONLEVEL`, computes the target MATK, and —
   only if it changed since the last tick — reapplies it through
   `bonus_script "bonus bMatk,<n>;"` with a short duration.
3. **The short duration** is kept alive by the loop refreshing it. Stop
   refreshing (unequip, log out, disable the mod and relog) and the buff
   expires in a handful of seconds.

`bonus_script` is used rather than a status-change (SC) so no visible buff
icon is added to the player's status bar, and so the bonus never fights with
a real food or potion buff for the same SC slot.

Because the loop is kicked off by `OnPCLoginEvent`, players logged in at the
moment the mod is enabled need to relog for the bonus to start applying — the
same "restart the server, then relog" flow the app already prompts for when
you tick the checkbox.

## Files

    refine-matk/
    ├── mod.json
    ├── README.md
    └── npc/
        └── refine_matk.txt

`npc/` only — the mod ships no `data/`, `System/` or `client/`, so
**Apply** restarts the server but not the whole app.
