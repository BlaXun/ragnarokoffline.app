# blaze-shield-drain

Turns on rAthena's `blaze_shield_drain` extension. That is the whole mod:
one entry in `db/extension_db.yml`, no scripts, no assets, no client
plugin.

## What flips on

`NJ_KAENSIN`'s pillar ticks route through `battle_drain()`, which is
otherwise called only from the weapon-attack path. Every item bonus in
the drain family then fires on each Blaze Shield hit for a Ninja
channelling the skill:

- `bonus bSPDrainValue,val` — the motivating case, Moonlight Dagger (3 SP per hit)
- `bonus bHPDrainValue,val`
- `bonus2 bSPDrainValueRace,race,val` and `bonus2 bHPDrainValueRace,race,val`
- `bonus2 bSPDrainValueClass,cls,val` and `bonus2 bHPDrainValueClass,cls,val`
- The drain-rate variants (`bSPDrainRate`, `bHPDrainRate`, and their race variants)

Gated on `sg->skill_id == NJ_KAENSIN` in `skill.cpp`, so Fire Wall
(which shares the `UNT_KAEN` branch through `UNT_FIREWALL`) is
untouched. Other Ninja skills and other placed magic skills are
untouched.

## Verifying

Roll a Ninja, learn Blaze Shield, equip Moonlight Dagger, cast the
skill on a group of Porings. With the mod off: SP only decreases. With
the mod on: SP ticks +3 per pillar hit and stays positive through a
full field of them.

## Requires

The extension is defined in rAthena — the app builds it when the vendor
pin is at or ahead of the commit that introduced `blaze_shield_drain`.
If the running build predates the extension, this mod parses fine and
does nothing: `extension_enabled()` returns false for unknown ids by
design, so a mod that names a not-yet-shipped extension fails safe
rather than throwing.

## Applying it

`db/` is read when the server starts. Settings → Restart server is
enough — no app restart, no rebuild.
