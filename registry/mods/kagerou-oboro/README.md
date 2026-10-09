# kagerou-oboro

Kagerou and Oboro in pre-renewal, reached by rebirth.

rAthena's server already knows both classes in a pre-renewal build: the job
ids, dual-wielding, the charms and every KO/OB skill are compiled in. What
pre-renewal lacks is the data: no HP, SP, EXP, ASPD or job-bonus tables for
them, no skill tree, item tables that let no Kagerou equip anything, skill
entries from an older revision, and no way to become one. This mod supplies
all of it, and changes nothing in rAthena or the app.

## The path

Talk to **Kirikage** in the Ninja guild (`que_ng`, beside Kuuga Gai):

1. **Ninja, base 99 / job 70** → reborn as a **Novice** at level 1. Like the
   Valkyrie's rebirth, you come with no items, no zeny and no unspent skill
   points, and you get First Aid, Play Dead, a Knife and a Cotton Shirt.
2. **Novice, job 10** with Basic Skill 9 → **Ninja** again, with 52 extra
   status points: the 100 a transcendent class starts with.
3. **Ninja, job 50 or later** → **Kagerou** (male) or **Oboro** (female).

Kagerou and Oboro go to job level 60. Their skill tree includes the Ninja's,
so every point goes wherever you like, and the total depends on when you
change:

| Change at Ninja job | Skill points (Novice + Ninja + Kagerou) |
|---|---|
| 50 | 9 + 49 + 59 = **117** |
| 60 | 9 + 59 + 59 = **127**, a transcendent class's total |
| 70 | 9 + 69 + 59 = **137**, ten below renewal's 147 (renewal's Kagerou goes to job 70) |

## How strong

A little below the transcendent classes:

- **HP**: the Assassin's table times 1.1. An Assassin Cross gets it times 1.25.
- **SP**: the Ninja's table times 1.1.
- **Job bonuses**: renewal's Kagerou bonuses to job 50, then five more, for
  +40 in all. A transcendent class gets +45.
- **EXP**: the transcendent tables, base and job.
- **ASPD**: the Ninja's, with a quicker Huuma Shuriken (700 against 750).
- **Cast times**: pre-renewal has no fixed cast time, and DEX shortens every
  cast to nothing at 150. Of the Kagerou/Oboro skills, only Distorted
  Crescent and Ominous Moonlight had one in renewal (2 s); both have 30 s
  cooldowns, so the whole 2 s is added to their cast time, which DEX and
  Izayoi reduce, as renewal's fixed-cast reductions did.
- **Skill damage**: scaled in `lua/kagerou_oboro.lua`, and Kunai Splash
  slowed in `db/skill_db.yml`, then measured on a pre-renewal server against
  an Assassin Cross (physical) and a High Wizard (magic) with the same
  level and weapon ATK, on the same target. Like the transcendent third
  classes, a fighter's area damage is held to about half of what it deals
  one target:

  | | Kagerou / Oboro | Transcendent class |
  |---|---|---|
  | Cross Slash + Soul Cutter | 872 dmg/s | Sonic Blow 1016 |
  | Swirling Petal (area, each target) | 440 | |
  | Kunai Splash (area, each target) | 488 | |
  | Kunai Explosion (area, ranged, each target) | 430 | |
  | Ice Spear, INT build, Oboro with Distorted Crescent | 2036 | Jupitel Thunder with Mystical Amplification 2197 |
  | Ice Spear, INT build, Kagerou | 1752 | |
  | Kamaitachi, INT build (area, each target) | 1545 | Meteor Storm with Mystical Amplification 1390 |

  A magical build casts the Ninja's spells, which are pre-renewal's and not
  changed here; as a caster's, its area spells are not held to half. The
  Oboro is the stronger caster and the Kagerou the stronger fighter, as in
  renewal: Shadow Warrior raises only physical damage, Distorted Crescent
  magic too.

  The Kagerou dual-wields daggers. Cross Slash leaves a Cross Wound, and a
  Cross Slash on a wounded target hits much harder (about 2,100 instead of
  754 per cast). Renewal means that for a Kagerou and an Oboro taking turns,
  but in rAthena your own wound counts too, so the 875 already includes it:
  without it, against a fresh target, the pair would do about 440. Other
  buffs (Shadow Warrior, Enchant Deadly Poison) are not counted. The runs behind the table are in
  `registry/tools/kagerou-oboro/balance.json`; to measure them again, see
  `registry/tools/expanded_class/balance/README.md`.

## Equipment

Four tiers, Kagerou/Oboro only, each a Huuma Shuriken, a Kodachi (a dagger,
for dual-wielding), a mask, a garb, a scarf, tabi and a charm. Mask, garb,
scarf and tabi of one tier give a set bonus.

| Tier | Level | Drops from |
|---|---|---|
| Kagemaru | 50 | Kapha, Green Maiden, Nine Tail, Dryad, Yao Jun |
| Tsukikage | 65 | Shinobi, Tengu, Evil Nymph, Baby Hatii, Zealotus |
| Yamigarasu | 80 | Wanderer, Cat o' Nine Tails, Eremes Guile, Dark Illusion, White Lady |
| Oborozuki | 95 | Samurai Specter, Evil Snake Lord, Assassin Cross Eremes, White Lady (MVP) |

The items borrow stock art (the Kitsune, Assassin, Kabuki and Dragon Arhat
masks, stock Huuma and dagger looks), so the mod ships no sprites.

Every item a Ninja can wear or use, a Kagerou and Oboro can too: the
equipment, shuriken and kunai, and awakening potions.

The **Shadow Supplier** beside Kirikage sells what the skills consume and
pre-renewal has no other source for: the four charms, Makibishi, Explosive
Kunai and Shadow Orbs. Kunai for Kunai Splash come from the Kunai Merchant
as usual.

## Files

| | |
|---|---|
| `npc/kagerou_oboro.txt` | Kirikage and the Shadow Supplier |
| `lua/kagerou_oboro.lua` | the skill damage scaling |
| `db/job_stats.yml` | the classes' HP, SP, EXP, bonuses, ASPD, weight |
| `db/skill_tree.yml` | renewal's Kagerou and Oboro trees |
| `db/skill_db.yml` | renewal's KO/OB skill entries, where pre-renewal's are an older revision without `Status:` |
| `db/item_db.yml` | `KagerouOboro` on the Ninja's items, and the equipment |
| `db/item_combos.yml` | the set bonuses |
| `db/mob_db.yml` | the equipment's drops |
| `System/itemInfo.lua` | the equipment's names and descriptions |

Everything under `db/` and `System/` is generated by
`registry/tools/kagerou-oboro/build.py`, a short description of the class run
by the shared `registry/tools/expanded_class/expanded_class.py`, from the
pinned rAthena and the three
CSV files beside it (`equipment.csv`, `drops.csv`, `combos.csv`). Edit those,
then rerun it:

```
python3 registry/tools/kagerou-oboro/build.py --rathena ../rathena
python3 registry/tools/kagerou-oboro/build.py --rathena ../rathena --check
```
