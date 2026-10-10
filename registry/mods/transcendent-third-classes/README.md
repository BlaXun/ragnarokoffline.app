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
| Sura | Champion | `valkyrie 55 42` |
| Ranger | Sniper | `valkyrie 42 55` |

The stock transcendent changers in the Valkyrie's hall stand in two rows.
Each third class's changer stands right beside its transcendent class's,
on the wall side.

The mod also carries renewal's **expanded classes**, which the stock
transcendent classes never had a counterpart for. Each is reached by
**rebirth** of its base class, the way a first class reaches its
transcendent class:

| Expanded class | Rebirth of | Where |
|---|---|---|
| Kagerou (male), Oboro (female) | Ninja | Kirikage, Ninja guild (`que_ng 33 62`) |
| Rebellion | Gunslinger | Old Hand Jesse, Gunslinger guild (`que_ng 156 167`) |
| Star Emperor | Star Gladiator | Master Haneul, Payon (`payon 160 141`) |
| Soul Reaper | Soul Linker | Shaman Seol, Payon (`payon 154 141`) |

Their damage follows the same rules as the third classes'.

### Area damage

Renewal gave almost every third class area attacks it could spam, and
levelling became gathering a crowd and pressing one button. In
pre-renewal area damage belongs to a few classes. So here a **fighting
third class deals at most about half its best single-target damage to
each target of an area**: an area attack pays from about three targets,
and against one or two its single-target skills stay better. The casters
whose job area damage is (the Warlock, like the High Wizard; the Soul
Reaper; a magical Kagerou or Oboro) are exempt.

### More skills to choose from

A third class keeps its second class's skills and adds its own, so it
chooses from more skills than its transcendent class (a Guillotine
Cross: the Assassin's and 19 of its own; an Assassin Cross: the
Assassin's and 5). It does not learn more: both have the same 69 skill
points from job levels, and its own skills need second-class skills
first (Cross Impact needs Sonic Blow 10). The wider choice is a real
advantage in flexibility, which the damage figures below do not
measure.

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
  | One target | Cross Impact 925 dmg/s; Rolling Cutter and Cross Ripper Slasher in turn 950 | Sonic Blow 1010 |
  | Area, per target | Rolling Cutter 468, in 7x7 | Meteor Assault 1176, in 5x5 |
  | Auto-attack, katar | 470 | 614 (Advanced Katar Mastery) |

  The Assassin Cross keeps the single-target crown, by about a tenth. The
  Guillotine Cross trades it for a wide (but, as an area attack, half as
  strong) Rolling Cutter, and for tools the Assassin Cross lacks:

  - **Rolling Cutter** builds up to ten counters; **Cross Ripper Slasher**,
    from up to 13 cells away, hits harder with each. The 950 above needs
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

Its Holy magic hits an area (Adoramus 7x7, Judex 3x3) for about half of
what a High Wizard's amplified Meteor Storm deals to each target (1255
to 1588 dmg/s, measured two ways): Adoramus 658 (it also costs a Blue
Gemstone), Judex 656.
Duple Light's magic strikes on a staff come to about 490 a second with
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
the Raido (Crush Strike), Berkana (Millennium Shield) and Nauthiz
(Refresh) runes get renewal's back.

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
| Area, per target | Wind Cutter 817, Ignition Break 711, Dragon Breath 743 | Bowling Bash's splash, Brandish Spear 417 |

- **Dragon Breath** is (current HP / 50 + max SP / 4) x level: it grows
  with HP, so a VIT Rune Knight with 20,000 HP breathes about a quarter
  harder than the figure above. It is scaled to 64%.
- **Giant Growth** (Thurisaz rune) gives STR +30, +250% on a Rune
  Knight's attacks and 2.5x damage on 30% of hits; renewal lets it run for
  15 minutes from one rune. Here it lasts **30 seconds and the rune can be
  used again after 3 minutes**: about 1900 dmg/s from auto-attacks while
  it lasts, a burst like Enchant Deadly Poison, not a state.
- **Crush Strike** makes the next hit one heavy blow (about 4600 here),
  once every 30 seconds.
- **Storm Blast** (Wyrd rune) hits everything around the Rune Knight for
  about 4400 each. Renewal lets a rune go every second, about 2200 dmg/s
  on each target from a stack of runes; here **one rune every 10
  seconds**, a burst of about 440 dmg/s a target on average.
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
| Area, per target | Overbrand 826, Earth Drive 864, Cannon Spear 871, Moon Slasher 803 | Grand Cross 667 (both have it) |

Renewal's Banishing Point did 6759 a second here and Overbrand 8928;
they are scaled to 25% and 9%. Its defensive skills are as in renewal.

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
staff, on the same target, without consumables, each spell at the pace
that got the most out of it:

| | Warlock | High Wizard |
|---|---|---|
| One target | Hell Inferno 1745 dmg/s, Tetra Vortex (with its four spheres) 1909, Soul Expansion 1904, Chain Lightning 1886 | Jupitel Thunder with Mystical Amplification 2008-2288 |
| Area, per target | Jack Frost 1512, Crimson Rock 1363, Frost Misty 1411, Comet 1409 | Meteor Storm with Mystical Amplification 1348-1396 |

Chain Lightning strikes at least four times, and on a lone target all four
land on it, so it is set as a single-target spell; in a pack its nine
strikes spread out.

- **SP.** A Warlock has no Soul Drain: about a sixth less SP and nothing
  back for a kill. At renewal's prices its area spells ran a full bar dry
  three times faster than an amplified Meteor Storm. Its costs here give
  about the same damage from a full SP bar: 235k-240k on one target
  against 257k for amplified Jupitel Thunder (before Soul Drain), and
  492k-513k on each target of an area against 642k for amplified Meteor
  Storm. Crimson Rock costs 42 SP at level 5, Jack Frost 39, Frost Misty
  47, Soul Expansion 28, Hell Inferno 49, Chain Lightning 60.
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

## Sura

### The path

1. Monk, base 99 / job 50 → the Valkyrie's rebirth → High Novice →
   High Acolyte. The rebirth remembers Champion as the target, as usual.
2. **High Acolyte, job 40 or later**, no unspent skill points: talk to the
   **Sura** beside the Champion changer instead of the Champion changer,
   which stays as it was. You are asked to confirm twice.

The class's skill tree is renewal's Sura tree: Novice, Acolyte, Monk and
the Sura's own skills, with a Champion's 69 job levels and skill points.
It keeps every Monk skill, Asura Strike among them, and never learns Zen,
Raging Palm Strike, Glacier Fist or Chain Crush Combo.

### Champion or Sura

- **Champion**, the one blow: Zen fills its spheres at once, the combos
  run into Asura Strike, and nothing hits harder.
- **Sura**, the endless chain: Dragon Combo, Knuckle Arrow and Tiger
  Cannon for steady damage, Gates of Hell as its burst, sweeping blows
  (Sky Net Blow, Earth Shaker, Rampage Blast, Lightning Ride) for crowds,
  and Gentle Touch to heal, steal SP or change its stats. Without Zen its
  spheres come one at a time, or from Raising Dragon.

### How strong

Measured against a Champion of the same level and stats, with the same
knuckle, on the same target, without consumables:

| | Sura | Champion |
|---|---|---|
| One target, steady | Knuckle Arrow 1024 dmg/s, Dragon Combo 1000, Tiger Cannon (with Raising Dragon) 1070 | Occult Impaction with Zen 1151 |
| Burst | Gates of Hell, about 12,700 a hit, once every 10 s | Asura Strike, about 19,500 a hit |
| Area, per target | Earth Shaker 510, Sky Net Blow 480, Lightning Ride 575, Rampage Blast 563 | |

Renewal's Knuckle Arrow did 3000 a second here, Dragon Combo 3900, Sky
Net Blow 4100 and Lightning Ride 4500; they are scaled in
`lua/third_classes.lua`. Tiger Cannon's damage comes mostly from HP and
SP, outside what a factor reaches, so its cooldown is 7 s instead of 3;
Gates of Hell, renewal's without a cooldown, has one of 10 s. Knuckle
Arrow and Dragon Combo cost about as much SP for their damage as a
Champion's Occult Impaction; Gates of Hell spends most of what is left,
as Asura Strike spends all of it.

### Equipment

Two tiers, two knuckles each, for both of the Monk's transcendent paths.
Each raises a Sura skill and a Champion skill (Knuckle Arrow and Occult
Impaction, Dragon Combo and Chain Crush Combo, and so on). Transcendent
classes only.

| Item | Level | Drops from |
|---|---|---|
| Rakshasa Claw | 70 | Owl Baron |
| Iron Mantra Knuckle | 70 | Owl Duke |
| Asura Fang | 90 | Tao Gunka |
| Vajra Knuckle | 90 | Eddga |
## Ranger

### The path

1. Hunter, base 99 / job 50 → the Valkyrie's rebirth → High Novice →
   High Archer. The rebirth remembers Sniper as the target, as usual.
2. **High Archer, job 40 or later**, no unspent skill points: talk to the
   **Ranger** beside the Sniper changer instead of the Sniper changer,
   which stays as it was. You are asked to confirm twice, and you are
   given a **Wolf's Flute**: Warg Mastery needs one held, as in renewal.
   Lost it? The Ranger gives another.

The class's skill tree is renewal's Ranger tree: Novice, Archer, Hunter
and the Ranger's own skills, with a Sniper's 69 job levels and skill
points. It keeps every Hunter skill and its falcon (the warg will not
come while a falcon is out), and never learns Falcon Assault, Sharp
Shooting, True Sight or Wind Walk.

Its traps take renewal's **Special Alloy Trap**, which no pre-renewal
shop sells: the **Trap Seller** beside Payon's Tool Dealer
(`payon_in01 7 49`) does, with the plain Trap.

### Sniper or Ranger

- **Sniper**, bow and falcon at long range: Falcon Assault, Sharp
  Shooting, True Sight, Wind Walk.
- **Ranger**, the wild: Aimed Bolt and Arrow Storm, a warg to fight with
  (Warg Strike, Warg Bite) and to ride, renewal's traps of fire, ice and
  steel, Camouflage, and Unlimit as a short burst window.

### How strong

Measured against a Sniper of the same level and stats, with the same
bow and arrows, on the same target, without consumables:

| | Ranger | Sniper |
|---|---|---|
| One target | Aimed Bolt 2212 dmg/s, Warg Strike 2393 | Double Strafe 2443 |
| Area, per target | Arrow Storm 1139, Cluster Bomb 954, Firing Trap 1291 (a trap set off with Detonator) | |

Renewal's Warg Strike did 7000 a second here, Aimed Bolt 3300 and Arrow
Storm 1700; they are scaled in `lua/third_classes.lua`. Traps do most of
their damage from DEX and INT, outside what a factor reaches: Cluster
Bomb's weapon part is scaled to 70%, Firing Trap's to 10%. **Unlimit**
more than triples ranged damage while it lasts, and renewal kept it up
for 150 s of every 300; here it lasts 30 s, a burst window (Aimed Bolt
6410 a second with it).

### Equipment

Two tiers, two bows each, for both of the Hunter's transcendent paths.
Each raises a Ranger skill and a Sniper skill (Aimed Bolt and Double
Strafe, Warg Strike and Falcon Assault, and so on). Transcendent classes
only.

| Item | Level | Drops from |
|---|---|---|
| Warden Bow | 70 | Ancient Worm |
| Pack Leader Bow | 70 | Mini Demon |
| Wildheart Longbow | 90 | Atroce |
| Garm Fang Bow | 90 | Garm |

## Kagerou and Oboro

Kagerou and Oboro in pre-renewal, reached by rebirth.

rAthena's server already knows both classes in a pre-renewal build: the job
ids, dual-wielding, the charms and every KO/OB skill are compiled in. What
pre-renewal lacks is the data: no HP, SP, EXP, ASPD or job-bonus tables for
them, no skill tree, item tables that let no Kagerou equip anything, skill
entries from an older revision, and no way to become one. This mod supplies
all of it, and changes nothing in rAthena or the app.

### The path

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

### How strong

At 0.85-1.0 of a transcendent class on one target, and for a fighter about
half of that on each target of an area (see *Area damage* above):

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
  | Ice Spear, INT build, ten water charms, Oboro with Distorted Crescent | 3184 | Jupitel Thunder with Mystical Amplification 2234 |
  | Ice Spear, the same, Kagerou | 2810 | |
  | Kamaitachi, INT build, ten wind charms (area, each target) | 2177 | Meteor Storm with Mystical Amplification 1326 |
  | The same against a warded monster (MDEF 40, INT 80, VIT 50): Oboro Ice Spear, Kagerou Ice Spear, Kamaitachi | 1677, 1398, 1390 | 1176, 799 |

  A magical build casts the Ninja's spells. Without charms a Kagerou or
  Oboro casts them exactly as a Ninja does. Charms (ten of one element, for
  five minutes) add to every ninjutsu of their element; at full strength,
  as in renewal, ten of them doubled the spells and put a charged Oboro at
  1.8 times a High Wizard. Here a Kagerou or Oboro keeps 48% of that bonus
  (`lua/kagerou_oboro.lua`), so ten charms still make Ice Spear about 1.6
  times as strong: a charged Kagerou casts at about 1.25 and an Oboro at
  about 1.4 times a High Wizard, also against well-warded monsters, where
  the Ninja's many small hits lose the most. Charms cost a cast and a charm
  item each. As a caster's, its area spells are not held to half. The Oboro
  is the stronger caster and the Kagerou the stronger fighter, as in
  renewal: Shadow Warrior raises only physical damage, Distorted Crescent
  magic too.

  The Kagerou dual-wields daggers. Cross Slash leaves a Cross Wound, and a
  Cross Slash on a wounded target hits much harder (about 2,100 instead of
  754 per cast). Renewal means that for a Kagerou and an Oboro taking turns,
  but in rAthena your own wound counts too, so the 875 already includes it:
  without it, against a fresh target, the pair would do about 440. Other
  buffs (Shadow Warrior, Enchant Deadly Poison) are not counted. The runs behind the table are in
  `registry/tools/transcendent-third-classes/balance-kagerou-oboro.json`; to measure them again, see
  `registry/tools/expanded_class/balance/README.md`.

### Equipment

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

## Rebellion

The Gunslinger's renewal advancement, **Rebellion**, in pre-renewal, reached
by rebirth.

rAthena's server already knows the class in a pre-renewal build: the job id
and every RL skill are compiled in. What pre-renewal lacks is the data: no
HP, SP, EXP, ASPD or job-bonus tables, no skill tree, item tables that let no
Rebellion use a gun, skill entries from an older revision, five consumables
the skills need, and no way to become one. This mod supplies all of it, and
changes nothing in rAthena or the app.

### The path

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

### How strong

At 0.85-1.0 of a transcendent class on one target, and for a fighter about
half of that on each target of an area (see *Area damage* above):

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

### Equipment

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

No monster drops two classes' gear (the build script refuses it), so each
stays within rAthena's ten drops per monster.

The items borrow stock art (stock gun looks, the Western Grace, Cowboy Hat
and Pirate Bandana), so the mod ships no sprites.

Every item a Gunslinger can wear or use, a Rebellion can too: guns, bullets,
grenades and the Gunslinger's gear.

The **Gunsmith** beside Jesse sells what the skills consume and pre-renewal
has no other source for: Full Metal Jacket, Grenade Launcher mines, Dragon
Tail Missile, Slug Bullet and Special Alloy Trap. Bullets and Silver Bullets
(for Platinum Alter) come from the stock gun shops.

## Star Emperor

**Star Emperor** in pre-renewal, as the Star Gladiator's rebirth: what Lord
Knight is to the Knight.

Pre-renewal never gave Star Gladiators a rebirth. rAthena's server already
knows the Star Emperor in a pre-renewal build: the class and every SJ skill
are compiled in, and it already lets the class wear what a Star Gladiator
wears and, as a third class, the transcendent-only items. What pre-renewal
lacks is the data: no HP, SP, EXP, ASPD or job-bonus tables, no skill tree,
skill entries from an older revision, and no way to become one. This mod
supplies it, and changes nothing in rAthena or the app.

### The path

Talk to **Master Haneul** beside Phoenix, the Taekwon master in Payon:

1. **Star Gladiator, base 99 / job 50** → reborn as a **Novice** at level 1.
   Like the Valkyrie's rebirth, you come with no items, no zeny and no
   unspent skill points, and you get First Aid, Play Dead, a Knife and a
   Cotton Shirt.
2. **Novice, job 10** with Basic Skill 9 → **Taekwon** again, with 52 extra
   status points: the 100 a transcendent class starts with.
3. **Taekwon, job 40 or later** → **Star Emperor**, which goes to job 70.

Like a transcendent class, the Star Emperor is the reborn second class: its
69 job levels buy Star Gladiator skills and Star Emperor skills alike (its
tree includes the Star Gladiator's).

| Change at Taekwon job | Skill points (Novice + Taekwon + Star Emperor) |
|---|---|
| 40 | 9 + 39 + 69 = **117** |
| 50 | 9 + 49 + 69 = **127**, a transcendent class's total |

Renewal's Star Emperor has 176 (a Star Gladiator's 49 on top).

### How strong

At 0.85-1.0 of a transcendent class on one target, and for a fighter about
half of that on each target of an area (see *Area damage* above):

- **HP and SP**: the Star Gladiator's tables times 1.1. A transcendent class
  gets its second class's table times 1.25.
- **Job bonuses**: renewal's Star Emperor bonuses, less the last three, for
  +40. A transcendent class gets +45.
- **EXP**: the transcendent tables, base and job.
- **ASPD and weight**: the Star Gladiator's.
- **Cast times**: pre-renewal has no fixed cast time, and DEX shortens every
  cast to nothing at 150. 75% of each skill's renewal fixed cast becomes
  after-cast delay, which DEX does not reduce, and the rest is added to its
  cast time: New Moon Kick casts in 1.25 s (before DEX) and then waits 0.75 s.
  A skill with a cooldown of 10 s or more cannot be spammed anyway, so its
  whole fixed cast goes into the cast time, where DEX reduces it: Nova
  Explosion, Star Emperor Advent, Book of Creating Star.
- **Gear**: everything a Star Gladiator wears, and the transcendent-only
  items (rAthena allows third classes those in pre-renewal).
- **Skill damage**: scaled in `lua/star_emperor.lua`, then measured on a
  pre-renewal server against an Assassin Cross with the same level, stats
  and weapon ATK, on the same target:

  | | Star Emperor | Assassin Cross |
  |---|---|---|
  | Prominence Kick (+ Solar Burst) | 943 dmg/s | Sonic Blow 1044 |
  | Attacks with Falling Star on Flash-Kicked targets | 907 | Sonic Blow 1044 |
  | New Moon Kick + Full Moon Kick (area, each target) | 459 | |

  Like the transcendent third classes, a fighter's area damage is held to
  about half of what it deals one target: renewal gave the kicks as much to
  every enemy around as to one.

  Nova Explosion, Star Emperor Advent, Gravity Control and the two Books work
  only on PvP and GvG maps, as in renewal, and are left as they are. Buffs
  and gear bonuses are not counted.

### Equipment

Four tiers, Star Emperor only, each a book, a hat, a dobok, a mantle, shoes
and a talisman. Hat, dobok, mantle and shoes of one tier give a set bonus;
the books raise the kicks.

| Tier | Level | Drops from |
|---|---|---|
| Dawn | 50 | Nightmare, Gargoyle, Knocker |
| Zenith | 65 | False Angel, Arc Angeling, Harpy |
| Eclipse | 80 | Fire Imp, Kasa, Gryphon |
| Celestial | 95 | Ifrit, Moonlight Flower, Valkyrie Randgris |

No monster drops two classes' gear (the build script refuses it), so each
stays within rAthena's ten drops per monster. The items borrow stock art (the Solar Hat, Crescent Helm, Moonlight
Flower Hat and Hat of the Sun God), so the mod ships no sprites.

## Soul Reaper

**Soul Reaper** in pre-renewal, as the Soul Linker's rebirth: what High
Wizard is to the Wizard.

Pre-renewal never gave Soul Linkers a rebirth. rAthena's server already
knows the Soul Reaper in a pre-renewal build: the class and every SP skill
are compiled in, and it already lets the class wear what a Soul Linker wears
and, as a third class, the transcendent-only items. What pre-renewal lacks
is the data: no HP, SP, EXP, ASPD or job-bonus tables, no skill tree, skill
entries from an older revision, and no way to become one. This mod supplies
it, and changes nothing in rAthena or the app.

### The path

Talk to **Shaman Seol** beside Phoenix, the Taekwon master in Payon:

1. **Soul Linker, base 99 / job 50** → reborn as a **Novice** at level 1.
   Like the Valkyrie's rebirth, you come with no items, no zeny and no
   unspent skill points, and you get First Aid, Play Dead, a Knife and a
   Cotton Shirt.
2. **Novice, job 10** with Basic Skill 9 → **Taekwon** again, with 52 extra
   status points: the 100 a transcendent class starts with.
3. **Taekwon, job 40 or later** → **Soul Reaper**, which goes to job 70.

Like a transcendent class, the Soul Reaper is the reborn second class: its
69 job levels buy Soul Linker skills (the spirits) and Soul Reaper skills
alike.

| Change at Taekwon job | Skill points (Novice + Taekwon + Soul Reaper) |
|---|---|
| 40 | 9 + 39 + 69 = **117** |
| 50 | 9 + 49 + 69 = **127**, a transcendent class's total |

### How strong

At 0.85-1.0 of a transcendent class on one target, and for a fighter about
half of that on each target of an area (see *Area damage* above):

- **HP and SP**: the Soul Linker's tables times 1.1. A transcendent class
  gets its second class's table times 1.25.
- **Job bonuses**: renewal's Soul Reaper bonuses, less the last three, for
  +40. A transcendent class gets +45.
- **EXP**: the transcendent tables, base and job.
- **Gear**: everything a Soul Linker wears, and the transcendent-only items.
- **Cast times**: pre-renewal has no fixed cast time, and DEX shortens every
  cast to nothing at 150. 75% of each skill's renewal fixed cast becomes
  after-cast delay, which DEX does not reduce, and the rest is added to its
  cast time: Espa casts in 0.75 s (before DEX) and then waits 0.75 s. A
  skill (or level) with a cooldown of 10 s or more cannot be spammed anyway,
  so its whole fixed cast goes into the cast time, where DEX reduces it: Soul
  Explosion, the Soul Reaper buff, Soul Unity from level 2.
- **Skill damage**: scaled in `lua/soul_reaper.lua`, then measured on a
  pre-renewal server against a High Wizard with the same level, stats and
  staff, on the same target:

  | | Soul Reaper | High Wizard |
  |---|---|---|
  | Espa | 1587 dmg/s | 1829 Jupitel Thunder, 986 Cold Bolt |
  | Espa + Eswhoo, soul energy refilled | 1567 | |
  | Soul Curse + Curse Explosion, soul energy refilled | about 5900 | |

  The aim is 0.85-1.0 of a transcendent class on one target, as for the
  transcendent third classes. As a caster's, the Soul Reaper's area spells
  are not held to half of that.

  Soul energy comes from Soul Collect (one every 20 s at level 5); the Soul
  Reaper buff only gains it against players. Espa costs none at level 10 and
  carries the damage; Eswhoo and Curse Explosion are bursts that spend it.
  Soul Division and Soul Explosion work only on PvP and GvG maps, as in
  renewal, and are left as they are.

### Equipment

Four tiers, Soul Reaper only, each a staff, a hood, a robe, a shawl, shoes
and a bell. Hood, robe, shawl and shoes of one tier give a set bonus; the
staves raise Espa, Eswhoo and Curse Explosion.

| Tier | Level | Drops from |
|---|---|---|
| Wisp | 50 | Wraith, Wind Ghost, Injustice |
| Shade | 65 | Gibbet, Dullahan, Disguise |
| Revenant | 80 | Loli Ruri, Bloody Murderer, Baroness of Retribution |
| Reaper's | 95 | Lord of the Dead, Dracula, Memory of Thanatos |

No monster drops two classes' gear (the build script refuses it), so each
stays within rAthena's ten drops per monster. The items borrow stock art (Morpheus's Hood, Whisper
Mask, Necromancer's Hood, Skull Hood), so the mod ships no sprites.

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
| `npc/sura.txt` | the Sura changer |
| `npc/ranger.txt` | the Ranger changer |
| `npc/trap_seller.txt` | the Trap Seller in Payon |
| `db/spellbook_db.yml` | renewal's spellbooks |
| `lua/third_classes.lua` | the third classes' skill damage scaling |
| `npc/kagerou_oboro.txt` | Kirikage and the Shadow Supplier |
| `lua/kagerou_oboro.lua` | the skill damage scaling |
| `npc/rebellion.txt` | Old Hand Jesse and the Gunsmith |
| `lua/rebellion.lua` | the skill damage scaling, with the measured table |
| `npc/star_emperor.txt` | Master Haneul |
| `lua/star_emperor.lua` | the skill damage scaling, with the measured table |
| `npc/soul_reaper.txt` | Shaman Seol |
| `lua/soul_reaper.lua` | the skill damage scaling, with the measured table |
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
`royal_guard/`, `warlock/`, `sura/`, `kagerou_oboro/`, `rebellion/`, `star_emperor/`,
`royal_guard/`, `warlock/`, `ranger/`, `kagerou_oboro/`, `rebellion/`, `star_emperor/`,
`soul_reaper/`):

```
python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena
python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena --check
```

The damage figures above come from the runs in
`registry/tools/transcendent-third-classes/balance.json` (the third
classes) and `balance-<class>.json` beside it (the expanded classes); to
measure them again, see `registry/tools/expanded_class/balance/README.md`:

```
python3 registry/tools/expanded_class/balance/run_specs.py registry/tools/transcendent-third-classes/balance.json
python3 registry/tools/expanded_class/balance/run_specs.py registry/tools/transcendent-third-classes/balance-kagerou-oboro.json
```
