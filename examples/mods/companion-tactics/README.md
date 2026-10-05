# companion-tactics

Recruited companions that fight by plan rather than by skill rotation. One table,
`db/population_strategy.yml`, and nothing else.
[docs/mods/companion-strategies.md](../../../docs/mods/companion-strategies.md)
is the reference.

**Status:** loaded by a real map-server in both eras, renewal and pre-renewal,
with no warnings (35 rules). Not yet played: the plans below are worked examples
of the format, and how well each one fights is still to be seen in game. Turn on
the population engine and recruit a companion first. The table does nothing
without one.

## What is in it

**Against any boss**, a companion never hits it from where it could not fight
back, which is what makes most bosses teleport: it steps to where the boss
could reach it, or holds off (`Reach: false`, `MoveTo: reachable`). **When a boss
teleports away** anyway, one companion says so and all of them regroup on their
owner (`On: encounter_ended`, `Reason: vanished`).

**Every fight, by role** (set in party chat, `<name> tank`): a tank provokes
whatever is hitting someone else, the support first, and keeps fighting it; two
tanks never take the same one. Attackers go for the boss rather than its slaves.
A Priest keeps Blessing on the tank.

**Every fight, Priests.** A party member about to take a Stun Attack gets a
Safety Wall before it lands (`On: monster_casts`, `Target: event`, once per
party). Anyone who types *wall me* in party chat gets one too. When a party
member dies, the Priest says it is coming. The engine's own resurrection does
the casting.

**Every fight, Wizards** stop casting at a monster with Magic Mirror up (a
strategy with `Rotation: false`) and start again when it drops. They walk onto a
party member's Land Protector, to where
it will land while the Sage is still casting it, or onto it once it is down, and
stay there while the owner moves about. **Sages** that see a Storm Gust coming
lay Land Protector at their feet and call the party (`Signal: on_me`), and
**everyone** comes when called. **Everyone** also steps out of a monster's ground
spell.

**The Stalactic Golem**, which has very high defence, a 1.5 s Stun Attack, and
Endure and Auto Guard when it is hit from range. It is an `Encounter`, so a
Priest with no target of its own still plays its part.

- *Every Monk and Champion* (a Champion uses its base class's entries) never
  throws spirit spheres at it (`Ban`), and steps out of its Stun Attack.
- *An Asura Monk or Champion* (`Build: asura`) is a four-state machine:
  `approach` (arrive with 5 spheres while the golem walks over), `fight`
  (Investigate, which does more the higher the defence), `finish` and `recover`
  (Steel Body, call for help). In `finish` it uses Fury, which costs all 5
  spheres, **charges again**, and then Asura Strike. A Monk casts Asura
  plainly. A Champion recharges with Zen (5 at once), hits plainly to open a
  combo, and strikes Asura straight out of Combo Finish or Chain Crush, where it
  has no cast time and needs fewer spheres.
- *A combo Monk or Champion* (`Build: combo`, which `Lacks` Asura Strike) only
  hits plainly (`Rotation: false`), so Triple Attack opens the combo. It then
  chains Chain Combo, Combo Finish, and Glacier Fist and Chain Crush if it has
  them. The steps are listed last first, and rAthena refuses one out of order.
  A spare sphere goes on Investigate, since combo damage suffers from the
  golem's defence.
- *A Final Strike Ninja and a Priest*, as a duo. Final Strike hits for the
  Ninja's current HP and leaves it at 1 HP (1 % in renewal), ending Soul. The
  Ninja casts Soul, then asks for Kyrie (`Signal: kyrie_me`) once nearly full,
  and strikes at full HP behind Kyrie or Cicada. It signals `struck`, then
  keeps its distance from the slow golem until healed. The Priest answers
  both signals (Kyrie on request, Heal the moment the Ninja struck), keeps
  everyone above 90 %, and stays out of the golem's reach.
- *A magic Ninja* stands in the middle of its own Blaze Shield (a ring of 24
  pillars) and draws the golem in with a level 1 Freezing Spear, so that the
  golem walks over the fire to reach it. It then uses Exploding Dragon. If the
  golem is low and pillars are left, it steps out the far side so the golem
  crosses the ring again. It keeps Cicada Skin Shed up below two blocks. Blaze Shield and
  Exploding Dragon are marked `Consume`. Catalysts are not paid yet (companions
  have no inventory of their own), so the marks take effect once inventories
  exist.

**Phreeoni**, the boss for the first playtest, for a Wizard, a Priest and an
Assassin beside their owner. It is an `Encounter`: the plan applies while
Phreeoni is near, whatever each companion is fighting. Its phases are strategies
switched on the boss's HP: `opening`, `stone` (below 80 %: Wide Stone Curse every
20 s, which cannot be outrun, so the Priest undoes it with Status Recovery) and
`last` (below 30 %: Power Up, then Hiding, which the Priest and Wizard reveal at
once). In every phase:
- the Wizard puts Meteor Storm (or Storm Gust) on the boss as it summons, so the
  Sandmen arrive in it, and again once three slaves stand around it (its Call
  Slave is instant, so only the result can be seen);
- one attacker takes slaves off the Priest;
- the Priest heals the most hurt, keeps Kyrie up and opens with Lex Aeterna;
- nobody uses Fire Wall, which sets off its Heaven's Drive;
- when the Priest dies and none is left, they fall back to their owner and stop
  fighting (a `fallback` strategy, entered with `Absent: { Ally: nearest, Job: Priest }`),
  until a Priest is up again;
- nobody casts anything the plan does not name: a plan about a monster turns the
  normal skill rotation off, so the Wizard casts Fire Bolt and its Meteors, the
  Assassin Enchant Poison and Sonic Blow (at the boss only, with SP to spare),
  and the Priest and Wizard keep their distance from Phreeoni.

**Regular AI characters** (`For: shells`): Wizards around the world keep Storm
Gust, Meteor Storm, Lord of Vermilion and Heaven's Drive for packs of three or
more, instead of casting them at a single monster.

**Porings and friends:** plain hits only, so neither companions nor the AI characters around them spend SP on them.

## Things worth knowing before copying it

- Cicada Skin Shed knocks the Ninja back each time it blocks, which moves it off
  the centre of its ring.
- A Defensive companion never starts a fight. The Ninja's pull only happens in
  Attack mode, or once the owner has hit the golem.
- The golem's Endure starts when it is hit from range, and Endure is what lets a
  monster walk over Blaze Shield without being held on a pillar.

Type `<companion name> trace` in party chat to see which rule it acts on and why.
