# transcendent-third-classes

Renewal's **third classes** in pre-renewal, as **sidegrades** of the
transcendent classes: a second way to finish a rebirth, with its own
skills, at the same strength.

After the Valkyrie's rebirth, a reborn first class normally becomes its
transcendent class. With this mod it can choose that class's third class
instead. The third class keeps every skill of its first and second class,
gets its own third-class skills, and **never** learns the transcendent
skills. Everything else is the transcendent class's: job levels, skill
points, HP, SP, EXP tables and gear. The choice is permanent.

rAthena's pre-renewal server already knows the third classes: the classes
and their skills are compiled in, and it lets a third class wear the
transcendent-only items. What pre-renewal lacks is the data (tables, a
skill tree, renewal's skill entries) and a way to become one. This mod
supplies it, and changes nothing in rAthena or the app.

The mod grows class by class. So far:

| Third class | Instead of | Changer |
|---|---|---|
| Guillotine Cross | Assassin Cross | beside the Valkyrie (`valkyrie 52 58`) |

## Guillotine Cross

### The path

1. Assassin, base 99 / job 50 → the Valkyrie's rebirth, choosing Assassin
   Cross as usual → High Novice → High Thief.
2. **High Thief, job 40 or later**, no unspent skill points: talk to the
   **Guillotine Cross** beside the Valkyrie instead of the usual Assassin
   Cross changer, which stays as it was. You are asked to confirm twice.

The class's skill tree is renewal's Guillotine Cross tree: Novice, Thief,
Assassin and the Guillotine Cross's own skills, with the 69 job levels of
an Assassin Cross. The skill points are the same as an Assassin Cross's.

### How strong

The same as an Assassin Cross, by construction or by measurement:

- **HP, SP, EXP, job levels**: the Assassin Cross's tables.
- **Job bonuses**: renewal's Guillotine Cross bonuses, topped up to +45,
  an Assassin Cross's total.
- **Gear**: everything an Assassin Cross wears, transcendent-only items
  included. Like an Assassin, it can carry a dagger in each hand.
- **Cast times**: 75% of each skill's renewal fixed cast becomes after-cast
  delay, which DEX does not reduce, and the rest is added to its cast time.
- **Skill damage**: scaled in `lua/third_classes.lua`, then measured on a
  pre-renewal server against an Assassin Cross of the same level, stats and
  weapon, on the same target, with no consumables:

  | | Guillotine Cross | Assassin Cross |
  |---|---|---|
  | One target | Cross Impact 937 dmg/s; Rolling Cutter and Cross Ripper Slasher in turn 964 | Sonic Blow 1023 |
  | Area, per target | Rolling Cutter 704, in 7x7 | Meteor Assault 1176, in 5x5 |
  | Auto-attack, katar | 470 | 614 (Advanced Katar Mastery) |

  The Assassin Cross keeps the single-target crown, by about a tenth. The
  Guillotine Cross trades it for a wider area, and for tools the Assassin
  Cross lacks:

  - **Rolling Cutter** builds up to ten counters; **Cross Ripper Slasher**,
    from up to 13 cells away, hits harder with each. The 964 above needs
    the two alternated as fast as the server takes them (about every
    0.35 s); at a relaxed pace it is nearer 690.
  - **Cross Impact** is the heavy hit. Renewal lets it fire twice a second;
    here its after-cast delay is 1.5 s at every level.
  - **Dark Crow** marks a target for 20 s, once a minute: melee attacks on
    it, the party's included, deal 30% more per level (half on bosses).
    Cross Impact and Cross Ripper Slasher are ranged, so it does not raise
    them.
  - **Weapon Blocking** parries a melee hit and opens **Counter Slash**
    (scaled like Cross Impact); **Hallucination Walk**, **Cloaking
    Exceed** and **Dark Illusion** are for survival and getting in.
  - **Poisons**: the new poisons are brewed from herbs, as in renewal,
    and put on the blade with Poisoning Weapon. Venom Pressure is scaled
    to 40% from its ratio; it needs a poison on the blade and was not
    measured.

### Equipment

Two tiers, a katar and a kris each. They suit both of the Assassin's
transcendent paths: each raises two Guillotine Cross skills and two
Assassin Cross skills, so whichever path a player chose, the weapon is
worth carrying. Transcendent classes only.

| Item | Level | Drops from |
|---|---|---|
| Venom Edge Katar | 70 | Medusa |
| Venom Edge Kris | 70 | Anubis |
| Guillotine Katar | 90 | Pharaoh |
| Guillotine Kris | 90 | Amon Ra |

The items borrow stock art, so the mod ships no sprites.

## Files

| | |
|---|---|
| `npc/guillotine_cross.txt` | the Guillotine Cross changer |
| `lua/third_classes.lua` | the skill damage scaling |
| `db/job_stats.yml` | HP, SP, EXP, bonuses, ASPD, weight |
| `db/skill_tree.yml` | renewal's trees, under the third classes |
| `db/skill_db.yml` | renewal's entries for the third-class skills, with the fixed cast times turned into delay |
| `db/item_db.yml` | the equipment |
| `db/item_combos.yml` | the set bonuses (none yet) |
| `db/mob_db.yml` | the equipment's drops |
| `System/itemInfo.lua` | the equipment's names and descriptions |

Everything under `db/` and `System/` is generated by
`registry/tools/transcendent-third-classes/build.py`, run by the shared
`registry/tools/expanded_class/expanded_class.py`, from the pinned rAthena
and the three CSV files beside it:

```
python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena
python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena --check
```
