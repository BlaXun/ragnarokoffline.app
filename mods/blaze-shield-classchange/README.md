# blaze-shield-classchange

Turns on rAthena's `blaze_shield_classchange` extension. That is the
whole mod: one entry in `db/extension_db.yml`, no scripts, no assets,
no client plugin.

## What flips on

`skill_additional_effect()`'s Polymorph gate widens from
`attack_type & BF_WEAPON` to
`(attack_type & BF_WEAPON) || skill_id == NJ_KAENSIN`. Any accessory
carrying `bonus bClassChange,rate` then rolls its polymorph on every
Blaze Shield pillar hit. The motivating item is Hylozoist Card
(`bonus bClassChange,100`) — 1% per hit to transform the target into a
random monster from `MOBG_BRANCH_OF_DEAD_TREE`. Under stock rAthena a
Ninja carrying Hylozoist never sees a proc; with this mod on, pillars
roll like weapon hits do.

Gated on `skill_id == NJ_KAENSIN`, so Fire Bolt, Meteor Storm and the
rest of the magic skill list stay stock — the intent was not to turn
Hylozoist Card into a general polymorph engine.

## Verifying

Roll a Ninja, equip an accessory with Hylozoist Card slotted (`@item 4321`
gives the card), cast Blaze Shield on a cluster of Porings. Roughly 1
in 100 pillar hits transforms the Poring under it.

## Requires

The extension is defined in rAthena — the app builds it when the vendor
pin is at or ahead of the commit that introduced
`blaze_shield_classchange`. If the running build predates the
extension, this mod parses fine and does nothing:
`extension_enabled()` returns false for unknown ids by design, so a
mod that names a not-yet-shipped extension fails safe rather than
throwing.

## Applying it

`db/` is read when the server starts. Settings → Restart server is
enough — no app restart, no rebuild.
