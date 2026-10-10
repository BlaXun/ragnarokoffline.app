# rebellion

The Gunslinger's renewal advancement, **Rebellion**, in pre-renewal, reached
by rebirth.

rAthena's server already knows the class in a pre-renewal build: the job id
and every RL skill are compiled in. What pre-renewal lacks is the data: no
HP, SP, EXP, ASPD or job-bonus tables, no skill tree, item tables that let no
Rebellion use a gun, skill entries from an older revision, five consumables
the skills need, and no way to become one. This mod supplies all of it, and
changes nothing in rAthena or the app.

## The path

Talk to **Old Hand Jesse** beside Master Miller, the Gunslinger job master
(`que_ng`):

1. **Gunslinger, base 99 / job 70** → reborn as a **Novice** at level 1. Like
   the Valkyrie's rebirth, you come with no items, no zeny and no unspent
   skill points, and you get First Aid, Play Dead, a Knife and a Cotton Shirt.
2. **Novice, job 10** with Basic Skill 9 → **Gunslinger** again, with 52 extra
   status points: the 100 a transcendent class starts with.
3. **Gunslinger, job 50 or later** → **Rebellion**, which goes to job 60.

Its skill tree includes the Gunslinger's. rAthena has the extra Gunslinger
levels spent on Gunslinger skills first, so the Rebellion's own skills always
get its 59 job levels:

| Change at Gunslinger job | Skill points (Novice + Gunslinger + Rebellion) |
|---|---|
| 50 | 9 + 49 + 59 = **117** |
| 60 | 9 + 59 + 59 = **127**, a transcendent class's total |
| 70 | 9 + 69 + 59 = **137**, ten below renewal's 147 |

## How strong

A little below the transcendent classes:

- **HP**: the Hunter's table times 1.1. A Sniper gets it times 1.25.
- **SP**: the Gunslinger's table times 1.1.
- **Job bonuses**: renewal's Rebellion bonuses to job 60, then three more, for
  +40 in all. A transcendent class gets +45.
- **EXP**: the transcendent tables, base and job.
- **ASPD and weight**: the Gunslinger's.
- **Cast times**: pre-renewal has no fixed cast time, and DEX shortens every
  cast to nothing at 150. 75% of each skill's renewal fixed cast becomes
  after-cast delay, which DEX does not reduce, and the rest is added to its
  cast time: Mass Spiral casts in 1.5 s (before DEX) and then waits 2.5 s.
- **Skill damage**: scaled in `lua/rebellion.lua`, then measured on a
  pre-renewal server against a Sniper with the same level, stats and weapon
  ATK, on the same target:

  | | Rebellion | Sniper |
  |---|---|---|
  | Rifle (Mass Spiral + Anti-Material Blast) | 2039-2309 dmg/s | Double Strafe 2448 |
  | Shotgun (Banishing Buster + Slug Shot + Shatter Storm) | 2203 | Double Strafe 2448 |
  | Grenade launcher (Howling Mine + Dragon Tail, marked target) | 2105 | Double Strafe 2448 |
  | Fire Dance, Round Trip, Fire Rain, Shatter Storm (area, each target) | 999-1088 | Sharp Shooting 814 |

  Each gun is aimed at 0.85-1.0 of a Sniper on one target, and the area
  skills at about half of the rifle on each target, the rule the
  transcendent third classes follow; at a Sniper's scale that still puts
  them above Sharp Shooting. Buffs (Heat Barrel, Platinum Alter, Improve Concentration)
  and gear bonuses are not counted.

## Equipment

Four tiers, Rebellion only, each a Revolver, a Rifle, a Gatling Gun, a
Shotgun, a Grenade Launcher, a hat, a coat, a poncho, boots and a badge. Hat,
coat, poncho and boots of one tier give a set bonus. Each gun raises the
skills that gun type is for.

| Tier | Level | Drops from |
|---|---|---|
| Dustwalker | 50 | Orc Archer, Obsidian, Remover, Mineral, Breeze |
| Bounty Hunter's | 65 | Apocalypse, Gig, Goblin Leader, Frus, Skogul |
| Outlaw's | 80 | Venatu, Dimik, Archdam, Cecil Damon, Howard Alt-Eisen |
| Hellfire | 95 | Sniper Cecil, Kiel D-01, RSX-0806, Whitesmith Howard, Lord Knight Seyren |

None of these monsters is one the kagerou-oboro mod also drops from, so both
mods can be on together without passing rAthena's ten drops per monster.

The items borrow stock art (stock gun looks, the Western Grace, Cowboy Hat
and Pirate Bandana), so the mod ships no sprites.

Every item a Gunslinger can wear or use, a Rebellion can too: guns, bullets,
grenades and the Gunslinger's gear.

The **Gunsmith** beside Jesse sells what the skills consume and pre-renewal
has no other source for: Full Metal Jacket, Grenade Launcher mines, Dragon
Tail Missile, Slug Bullet and Special Alloy Trap. Bullets and Silver Bullets
(for Platinum Alter) come from the stock gun shops.

## Files

| | |
|---|---|
| `npc/rebellion.txt` | Old Hand Jesse and the Gunsmith |
| `lua/rebellion.lua` | the skill damage scaling, with the measured table |
| `db/job_stats.yml` | the class's HP, SP, EXP, bonuses, ASPD, weight |
| `db/skill_tree.yml` | renewal's Rebellion tree |
| `db/skill_db.yml` | renewal's RL skill entries, where pre-renewal's are an older revision without `Status:`, with every field and flag pre-renewal sets and renewal does not cleared |
| `db/item_db.yml` | `Rebellion` on the Gunslinger's items, renewal's ammunition the skills need, and the equipment |
| `db/item_combos.yml` | the set bonuses |
| `db/mob_db.yml` | the equipment's drops |
| `System/itemInfo.lua` | the equipment's names and descriptions |

Everything under `db/` and `System/` is generated by
`registry/tools/rebellion/build.py`, a short description of the class run by
the shared `registry/tools/expanded_class/expanded_class.py`, from the pinned
rAthena and the three CSV
files beside it (`equipment.csv`, `drops.csv`, `combos.csv`). Edit those,
then rerun it:

```
python3 registry/tools/rebellion/build.py --rathena ../rathena
python3 registry/tools/rebellion/build.py --rathena ../rathena --check
```

The damage figures above come from the runs in
`registry/tools/rebellion/balance.json`; to measure them again, see
`registry/tools/expanded_class/balance/README.md`:

```
python3 registry/tools/expanded_class/balance/run_specs.py registry/tools/rebellion/balance.json
```

`docs/mods/EXPANDED_CLASS_REBIRTH.md` (on the kagerou-oboro branch) is the
guide this mod follows.
