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
| Guillotine Cross | Assassin Cross | `valkyrie 42 58` |
| Shadow Chaser | Stalker | `valkyrie 55 58` |
| Arch Bishop | High Priest | `valkyrie 42 42` |
| Rune Knight | Lord Knight | `valkyrie 42 39` |
| Royal Guard | Paladin | `valkyrie 55 39` |
| Warlock | High Wizard | `valkyrie 42 47` |

The stock transcendent changers in the Valkyrie's hall stand in two rows.
Each third class's changer stands right beside its transcendent class's,
on the wall side.

## Guillotine Cross

### The path

1. Assassin, base 99 / job 50 → the Valkyrie's rebirth, choosing Assassin
   Cross as usual → High Novice → High Thief.
2. **High Thief, job 40 or later**, no unspent skill points: talk to the
   **Guillotine Cross** beside the Assassin Cross changer instead of the
   Assassin Cross changer, which stays as it was. You are asked to confirm twice.

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

## Shadow Chaser

### The path

1. Rogue, base 99 / job 50 → the Valkyrie's rebirth → High Novice → High
   Thief. The rebirth remembers Stalker as the target, as usual.
2. **High Thief, job 40 or later**, no unspent skill points: talk to the
   **Shadow Chaser** beside the Stalker changer instead of the Stalker
   changer, which stays as it was. You are asked to confirm twice.

The class's skill tree is renewal's Shadow Chaser tree: Novice, Thief,
Rogue and the Shadow Chaser's own skills, with a Stalker's 69 job levels
and skill points. It never learns Preserve, Full Strip, Reject Sword or
Chase Walk.

### Two stolen skills, no Preserve

A Stalker keeps one stolen skill for good with Preserve. A Shadow Chaser
has two slots instead:

- **Plagiarism**, as a Rogue's: every copyable skill that hits you
  replaces it.
- **Reproduce**: for five minutes after you cast it, a copyable skill that
  hits you goes into its own slot, at Reproduce's level (capped at what
  the caster used). Outside those five minutes nothing replaces it, so
  this is the slot you choose. It copies first and second class skills
  too, not only third class ones.

**Auto Shadow Spell** then casts a stolen spell by itself on your
attacks, at (its level + 5) / 2, no higher than the level you stole. It
takes Mage and Wizard spells and Heal, as in renewal, and this mod adds
**Turn Undead** and three ninjutsu: **Flaming Petals**, **Freezing
Spear** and **Wind Blade**. rAthena never auto-casts Holy Light or Magnus
Exorcismus, and the self-centred and catalyst ninjutsu would not place or
would cast for free, so those are left out.

### How strong

Same tables, same gear, measured against a Stalker of the same level and
stats, with the same weapon, on the same target, with no consumables:

| | Shadow Chaser | Stalker |
|---|---|---|
| Bow (DEX build) | Triangle Shot 2243 dmg/s | Double Strafe 2280 |
| Dagger (STR build), one target | Fatal Menace 1076, on every target around it | auto-attack 651; Back Stab only from behind, once |
| Burst | Feint Bomb about 2200 a blast, every 5 s | |

- **Triangle Shot** is the main attack, at a Stalker's Double Strafe.
- **Fatal Menace** hits an area for about what Meteor Assault does per
  target (1176), which no Stalker skill of its own does.
- **Feint Bomb** leaves a decoy that draws monsters off you, throws you
  back and blasts for about two Triangle Shots. It costs a Paint Brush and
  a Surface Paint.
- **Invisibility** lets you attack while hidden, but turns your attacks
  Ghost, so it is for Ghost-weak targets and escapes, not damage.
- The **Masquerades**, **Shadow Form**, **Strip Accessory**, **Body
  Painting** and the ground skills (**Man Hole**, **Dimension Door**,
  **Chaos Panic**, **Maelstrom**, **Bloody Lust**) are as in renewal.
- What a Stalker keeps instead: one stolen skill kept for good, Full
  Strip, Reject Sword and Chase Walk.

### Equipment

Two tiers, a dagger and a bow each, for both of the Rogue's transcendent
paths. Each raises Back Stab or Double Strafe for everyone, the same skill
further for a Stalker, and Fatal Menace or Triangle Shot for a Shadow
Chaser. Transcendent classes only.

| Item | Level | Drops from |
|---|---|---|
| Cutpurse's Stiletto | 70 | Ancient Mimic |
| Trickster's Bow | 70 | Raydric Archer |
| Nightshade Dirk | 90 | Nightmare Terror |
| Phantom Longbow | 90 | Banshee Master |

## Arch Bishop

### The path

1. Priest, base 99 / job 50 → the Valkyrie's rebirth → High Novice → High
   Acolyte. The rebirth remembers High Priest as the target, as usual.
2. **High Acolyte, job 40 or later**, no unspent skill points: talk to the
   **Arch Bishop** beside the High Priest changer instead of the High Priest
   changer, which stays as it was. You are asked to confirm twice.

The class's skill tree is renewal's Arch Bishop tree: Novice, Acolyte,
Priest and the Arch Bishop's own skills, with a High Priest's 69 job
levels and skill points. It never learns Assumptio, Basilica, Meditatio
or Mana Recharge.

### High Priest or Arch Bishop

- **High Priest**, the guardian: Assumptio halves the damage one person
  takes, Basilica shuts out attacks, Meditatio and Mana Recharge make its
  SP last. The priest for boss fights and tanks.
- **Arch Bishop**, the party leader and battle priest: buffs for the whole
  party in one cast (Clementia: Blessing, Canto Candidus: Increase AGI,
  Praefatio: Kyrie Eleison, Expiatio, Sacrament), heals for the whole
  party (Coluceo Heal) and a big single heal (Highness Heal), Renovatio,
  Epiclesis, the Laudas, Silentium, Oratio, Clearance, and Holy magic
  (Adoramus, Judex) and Duple Light for fighting. The priest for groups
  and levelling.

### How strong

Measured on a pre-renewal server with the same level, stats and staff,
on the same target. Renewal prices the Arch Bishop's own skills for
renewal's larger SP pools; on a High Priest's pool, without Meditatio or
Mana Recharge, it could keep up only half of a High Priest's healing. This
mod lowers those costs (the heal amounts and durations are renewal's):

| | Renewal SP | Here |
|---|---|---|
| Clementia 3 | 360 | 256: what five Blessings cost a High Priest |
| Canto Candidus 3 | 240 | 192: five Increase AGIs |
| Praefatio 10 | 180 | 140: five Kyries |
| Highness Heal 5 | 190 | 80 |
| Coluceo Heal 3 | 240 | 110 |

In a party of five, buffs kept up and Magnificat doubling SP recovery:

| | High Priest | Arch Bishop |
|---|---|---|
| Max SP, SP recovered a minute standing | 2326, 888 | 2125, 752 |
| Buff upkeep, SP a minute | 232 | 209 |
| HP healed per SP | Heal 82 | Highness Heal 88, Coluceo Heal on five 100, Heal 55 |
| Healing it can keep up, against a High Priest | | 0.89 on one person, 1.02 on the party |

Its Holy magic is scaled to about 0.7 of a High Wizard's Cold Bolt (847
dmg/s): Adoramus 636 (it also costs a Blue Gemstone), Judex 564. Duple
Light's magic strikes on a staff come to about 490 a second with
auto-attacks, below casting; its melee strike, for a STR battle priest,
is as in renewal.

### Equipment

Two tiers, a mace and a staff each, for both of the Priest's transcendent
paths. Each mace raises damage against Undead and Demons for everyone, by
the same again for a High Priest, and Duple Light's melee strike for an
Arch Bishop; each staff raises MATK and healing for everyone, healing
again for a High Priest, and Adoramus for an Arch Bishop. Transcendent
classes only.

| Item | Level | Drops from |
|---|---|---|
| Censer Mace | 70 | Khalitzburg |
| Pilgrim's Rod | 70 | Evil Druid |
| Grand Censer | 90 | Dark Priest |
| Staff of Absolution | 90 | Necromancer |

## Rune Knight

### The path

1. Knight, base 99 / job 50 → the Valkyrie's rebirth → High Novice → High
   Swordman. The rebirth remembers Lord Knight as the target, as usual.
2. **High Swordman, job 40 or later**, no unspent skill points: talk to the
   **Rune Knight** beside the Lord Knight changer instead of the Lord Knight
   changer, which stays as it was. You are asked to confirm twice.

The class's skill tree is renewal's Rune Knight tree: Novice, Swordman,
Knight and the Rune Knight's own skills, with a Lord Knight's 69 job
levels and skill points. It never learns Spiral Pierce, Frenzy, Aura
Blade, Concentration, Parrying, Tension Relax, Head Crush or Joint Beat.

**The dragon.** Dragon Breath is cast from a dragon. Renewal's Dragon
Breeder is not on a pre-renewal server, and the Peco Peco Breeder gives a
Rune Knight a Peco Peco, so this mod adds a **Dragon Breeder** beside the
Knights' Peco Peco Breeder in Prontera (`prontera 55 353`). It is free,
and takes the dragon back when you talk to it again.

**Rune stones.** Rune Mastery cuts them from the materials pre-renewal
already has recipes for. Pre-renewal's rune items have no reuse delay;
the Raido (Crush Strike), Berkana (Millennium Shield), Nauthiz (Refresh)
and Wyrd (Storm Blast) runes get renewal's back.

### Lord Knight or Rune Knight

- **Lord Knight**, the duellist: Spiral Pierce, Frenzy, Aura Blade,
  Concentration, Parrying. The best single target.
- **Rune Knight**, the dragon rider and front-line fighter: Dragon Breath,
  Ignition Break and Wind Cutter for crowds, Sonic Wave and Hundred Spear
  for one target, Death Bound, Dragon Howling, and the runes.

### How strong

Measured against a Lord Knight of the same level and stats, on the same
target, without consumables. Spiral Pierce is measured with a spear of a
Lance's weight, since in pre-renewal its damage comes from the weight.

| | Rune Knight | Lord Knight |
|---|---|---|
| One target | Sonic Wave 1415 dmg/s, Hundred Spear 1450 | Spiral Pierce 1562, Bowling Bash 1359 (both have it), Frenzy auto-attacks 1087 |
| Area, per target | Wind Cutter 1222, Ignition Break 1198, Dragon Breath 991 | Bowling Bash's splash, Brandish Spear 417 |

- **Dragon Breath** is (current HP / 50 + max SP / 4) x level: it grows
  with HP, so a VIT Rune Knight with 20,000 HP breathes about a quarter
  harder than the figure above. It is scaled to 85%.
- **Giant Growth** (Thurisaz rune) gives STR +30, +250% on a Rune
  Knight's attacks and 2.5x damage on 30% of hits; renewal lets it run for
  15 minutes from one rune. Here it lasts **30 seconds and the rune can be
  used again after 3 minutes**: about 1900 dmg/s from auto-attacks while
  it lasts, a burst like Enchant Deadly Poison, not a state.
- **Crush Strike** makes the next hit one heavy blow (about 4600 here),
  once every 30 seconds.
- **Storm Blast** hits nothing on this rAthena build in pre-renewal, with
  either era's skill entry. It is left as it is.
- The other runes (Millennium Shield, Stone Hard Skin, Fighting Spirit,
  Vitality Activation, Abundance, Refresh) are as in renewal.

### Equipment

Two tiers, a two-handed sword and a two-handed spear each, for both of
the Knight's transcendent paths. Each sword raises Bowling Bash for
everyone, again for a Lord Knight, and Sonic Wave for a Rune Knight; each
spear raises Brandish Spear for everyone, Spiral Pierce for a Lord Knight
and Hundred Spear for a Rune Knight. The spears are as heavy as a Lance,
for Spiral Pierce. The second tier cannot break, which Giant Growth would
otherwise risk. Transcendent classes only.

| Item | Level | Drops from |
|---|---|---|
| Runeblade | 70 | Raydric |
| Dragonfang Pike | 70 | Skeleton General |
| Rune Greatsword | 90 | Abysmal Knight |
| Wyrmguard Lance | 90 | Bloody Knight |

## Royal Guard

### The path

1. Crusader, base 99 / job 50 → the Valkyrie's rebirth → High Novice →
   High Swordman. The rebirth remembers Paladin as the target, as usual.
2. **High Swordman, job 40 or later**, no unspent skill points: talk to the
   **Royal Guard** beside the Paladin changer instead of the Paladin
   changer, which stays as it was. You are asked to confirm twice.

The class's skill tree is renewal's Royal Guard tree: Novice, Swordman,
Crusader and the Royal Guard's own skills, with a Paladin's 69 job levels
and skill points. It never learns Rapid Smiting, Martyr's Reckoning,
Gloria Domini or Battle Chant. A mounted Royal Guard rides a gryphon,
from the Crusaders' Peco Peco Breeder as before.

### Paladin or Royal Guard

- **Paladin**, the holy striker and martyr: Rapid Smiting, Martyr's
  Reckoning, Gloria Domini, Battle Chant. The best single target.
- **Royal Guard**, the shield wall: spear sweeps (Overbrand, Cannon Spear,
  Moon Slasher), shield blows (Shield Press, Earth Drive, Shield Spell),
  and protection (Reflect Damage, Prestige, King's Grace, Piety, Force of
  Vanguard). Inspiration is a large all-round buff that costs EXP, HP
  and SP. Banding, Ray of Genesis and Hesperus Lit want other Royal Guards
  beside it, as in renewal (Inspiration lets one cast Ray of Genesis
  alone).

### How strong

Measured against a Paladin of the same level and stats, with the same
spear and a shield of a Stone Buckler's weight (Rapid Smiting and Shield
Press grow with it), on the same target, without consumables:

| | Royal Guard | Paladin |
|---|---|---|
| One target | Banishing Point 1747 dmg/s, Shield Press 1224 | Rapid Smiting 1903, Holy Cross 1690 (both have it) |
| Area, per target | Overbrand 1013, Earth Drive 943, Cannon Spear 935, Moon Slasher 802 | Grand Cross 667 (both have it) |

Renewal's Banishing Point did 6759 a second here and Overbrand 8928;
they are scaled to 25% and 11%. Its defensive skills are as in renewal.

### Equipment

Two tiers, a spear and a shield each, for both of the Crusader's
transcendent paths. Each spear raises Holy Cross for everyone, again for
a Paladin, and Banishing Point for a Royal Guard; each shield raises
Shield Boomerang for everyone, Rapid Smiting for a Paladin and Shield
Press for a Royal Guard. The shields are heavy, since Rapid Smiting and
Shield Press grow with a shield's weight. Transcendent classes only.

| Item | Level | Drops from |
|---|---|---|
| Vanguard Spear | 70 | Zombie Master |
| Bulwark Shield | 70 | Ancient Mummy |
| Royal Partisan | 90 | Wraith Dead |
| Aegis of the Guard | 90 | Seyren Windsor |

## Warlock

### The path

1. Wizard, base 99 / job 50 → the Valkyrie's rebirth → High Novice → High
   Mage. The rebirth remembers High Wizard as the target, as usual.
2. **High Mage, job 40 or later**, no unspent skill points: talk to the
   **Warlock** beside the High Wizard changer instead of the High Wizard
   changer, which stays as it was. You are asked to confirm twice.

The class's skill tree is renewal's Warlock tree: Novice, Mage, Wizard and
the Warlock's own skills, with a High Wizard's 69 job levels and skill
points. It never learns Mystical Amplification, Soul Drain, Gravitation
Field, Ganbantein, Napalm Vulcan or Magic Crasher.

### High Wizard or Warlock

- **High Wizard**, the storm-caller: the Wizard's spells made greater by
  Mystical Amplification, Soul Drain for SP, Gravitation Field and
  Ganbantein for bosses and sieges. The best single target, and the one
  that never runs dry while it kills with single-target spells.
- **Warlock**, the elementalist: spells of its own (Comet, Crimson Rock,
  Hell Inferno, Chain Lightning, Earth Strain, Tetra Vortex, Soul
  Expansion, Jack Frost, Frost Misty, Drain Life), control (White
  Imprison, Stasis, Marsh of Abyss, Sienna Execrate), and stored spells:
  elemental spheres and spellbooks that Release fires without a cast.

### Spellbooks

Reading Spellbook works renewal's way: use a **spellbook**, which reads it
(a 5 s cast), and the spell is stored; **Release** at level 1 casts it at
once. The books are sold by the **Spellbook Seller** in the Geffen magic
school (`geffen_in 175 112`), where renewal's Lea stands, at renewal's
prices: 100,000 zeny for Storm Gust, Lord of Vermilion and Meteor Storm,
500,000 for Drain Life, Jack Frost, Earth Strain, Crimson Rock and Chain
Lightning, 1,000,000 for Comet and Tetra Vortex. A book is not used up.
Pre-renewal has none of this (its own Reading Spellbook does nothing on
rAthena), so the books, the reading skill and the spellbook table come
from renewal.

### How strong

Measured against a High Wizard of the same level and stats, with the same
staff, on the same target, one cast at a time, without consumables:

| | Warlock | High Wizard |
|---|---|---|
| One target | Hell Inferno 1926 dmg/s, Tetra Vortex (with its four spheres) 1995, Soul Expansion 1836 | Jupitel Thunder 1750, with Mystical Amplification 2032 |
| Area, per target | Jack Frost 1390, Crimson Rock 1280, Chain Lightning 1259, Frost Misty 1249, Comet 1409 | Meteor Storm 960, with Mystical Amplification 1255 |

- **SP.** A Warlock has no Soul Drain: about a sixth less SP and nothing
  back for a kill. At renewal's prices its area spells ran a full bar dry
  three times faster than an amplified Meteor Storm. Its costs here give
  about the same damage from a full SP bar: 235k-240k on one target
  against 257k for amplified Jupitel Thunder (before Soul Drain), and
  492k-513k on each target of an area against 642k for amplified Meteor
  Storm. Crimson Rock costs 42 SP at level 5, Jack Frost 39, Frost Misty
  47, Soul Expansion 28, Hell Inferno 79.
- **Comet** keeps pre-renewal's cost of **2 Red Gemstones** (an import
  entry cannot take an item cost away), with renewal's 20 second cooldown.
- **Area is the Warlock's job**, as it is the High Wizard's.

### Equipment

Two tiers, a staff and a two-handed staff each, for both of the Wizard's
transcendent paths. Each staff raises Jupitel Thunder for everyone, again
for a High Wizard, and Chain Lightning for a Warlock; each two-handed
staff raises Lord of Vermilion for everyone, again for a High Wizard, and
Crimson Rock for a Warlock. All give MATK +15%. Transcendent classes only.

| Item | Level | Drops from |
|---|---|---|
| Elemental Rod | 70 | Elder |
| Ember Staff | 70 | Incubus |
| Arcane Conduit | 90 | Succubus |
| Staff of Starfall | 90 | Kathryne Keyron |

## Files

| | |
|---|---|
| `npc/guillotine_cross.txt` | the Guillotine Cross changer |
| `npc/shadow_chaser.txt` | the Shadow Chaser changer |
| `npc/arch_bishop.txt` | the Arch Bishop changer |
| `npc/rune_knight.txt` | the Rune Knight changer |
| `npc/dragon_breeder.txt` | the Dragon Breeder in Prontera |
| `npc/royal_guard.txt` | the Royal Guard changer |
| `npc/warlock.txt` | the Warlock changer |
| `npc/spellbook_seller.txt` | the Spellbook Seller in Geffen |
| `db/spellbook_db.yml` | renewal's spellbooks |
| `lua/third_classes.lua` | the skill damage scaling |
| `db/job_stats.yml` | HP, SP, EXP, bonuses, ASPD, weight |
| `db/skill_tree.yml` | renewal's trees, under the third classes |
| `db/skill_db.yml` | renewal's entries for the third-class skills, with the fixed cast times turned into delay, the Arch Bishop's lower SP costs, and the Auto Shadow Spell flag on four more spells |
| `db/item_db.yml` | the equipment, the rune stones' reuse delays, and renewal's spellbooks |
| `db/item_combos.yml` | the set bonuses (none yet) |
| `db/mob_db.yml` | the equipment's drops |
| `System/itemInfo.lua` | the equipment's names and descriptions |

Everything under `db/` and `System/` is generated by
`registry/tools/transcendent-third-classes/build.py`, run by the shared
`registry/tools/expanded_class/expanded_class.py`, from the pinned rAthena
and each class's three CSV files, in its own directory beside it
(`guillotine_cross/`, `shadow_chaser/`, `arch_bishop/`, `rune_knight/`,
`royal_guard/`, `warlock/`):

```
python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena
python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena --check
```
