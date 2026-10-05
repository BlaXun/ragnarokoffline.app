# How companions fight: strategies

A recruited companion casts from its class's skill list in rotation, whatever it
is fighting. A mod can give it a plan instead: rules for a particular monster,
job and build, in a table the population engine reads,
`db/population_strategy.yml`.

This page is the reference for that table.
[`examples/mods/companion-tactics`](../../examples/mods/companion-tactics) is a
working set of plans: two Monk builds and a Ninja against the Stalactic Golem, a
Priest who walls party members about to be stunned, and plain hits on Porings.

By default only **recruited companions** use these rules. A plan marked
`For: shells` or `For: all` is used by the regular AI characters around the world
as well ([Regular shells](#regular-shells)). With no rules loaded the engine
behaves exactly as it did before. The engine ships the table empty.

## The shape

```yaml
Header:
  Type: POPULATION_STRATEGY_DB
  Version: 1

Body:
  - Mob: STALACTIC_GOLEM          # AegisName, id, or All; Mobs: [..] for several
    Targeting: { Priority: 50 }   # optional
    Jobs:
      - Job: Monk                 # Monk, High_Priest, JOB_NINJA, 15, or All
        Build: combo              # optional: one way to play the job
        Requires: { Skills: [MO_CHAINCOMBO], Lacks: [MO_EXTREMITYFIST] }
        Rotation: false           # optional: the normal skill rotation (see below)
        Ban: [MO_FINGEROFFENSIVE] # optional: these rotation skills not against it
        Start: approach           # the strategy each new fight starts in
        Rules: [...]              # rules for every strategy
        Strategies:
          - Name: approach
            Rules: [...]
          - Name: fight
            Rules: [...]
```

A monster, a job and a build together make a **plan**. A companion uses every
plan that matches what it is fighting:

1. the monster it targets, then any **encounter** monster near it (below), then
   `Mob: All`;
2. its own job before its base class (rAthena's `get_base_job`), before `Job: All`;
3. within those, each `Build` whose `Requires` it meets, before the entry
   without a `Build`.

### Encounters: boss fights

A monster's plan normally applies only while the companion targets that monster.
In a boss fight that is too narrow: the Priest heals with no target at all, and
the Wizard spends half the fight on the slaves. `Encounter: true` makes the
monster's plans apply while one is within 14 cells of the companion, whatever it
is fighting:

```yaml
- Mob: PHREEONI
  Encounter: true
  Jobs: [...]
```

The plan's strategy starts over with each new boss, not with each new target.
Its `enemy_*` conditions still ask about the companion's current target, which
may be a slave; ask about the boss with a selector:
`Target: { Enemy: boss }` and `When: enemy_hp_pct_lt80`.
[`examples/mods/companion-tactics`](../../examples/mods/companion-tactics) has a
whole Phreeoni encounter.

## Rules

Every turn (every 100 ms while it fights) the companion goes down its rules,
highest `Priority` first, and does what the first one that applies says. Ties go
to the more specific plan, then to file order. Nothing is random: the same
situation always gives the same decision.

A rule applies when all of the following hold:

| Key | The rule applies only... |
|---|---|
| `Requires: { Skills, Lacks, Items, BaseLevel, Role }` | to a companion that has (and lacks) these. `Role` is the party role set in chat (`tank`, `support`, `attacker`, `none`). A `Cast` rule also requires the skill itself, so a rule for a skill the companion never learned does not exist for it. |
| `On:` | within `Within` ms (default 3000) of an event, and once per event. See [Events](#events). |
| `When:` | while a condition holds. The syntax is `population_skill_db.yml`'s: `enemy_hp_pct_lt30`, `self_spheres_ge1`, `not_enemy_aeterna`, `[a, b]` for AND, `{ OR: [a, b] }`. `ally_*` asks about the rule's own target and `master_*` about the owner. |
| `Charges: { Status, Below \| AtLeast, Value }` | while a status's counter is in range. Cicada Skin Shed keeps its blocks left in its second value (the default), so `{ Status: SC_UTSUSEMI, Below: 2 }` is "1 or 0 left". No status counts as 0. |
| `Field: { Skill, Below \| AtLeast, Range, Owner, At }` | while that many ground units of the skill stand within `Range` cells (default 5; `0` is the cell itself) of the companion, or with `At: target` of the rule's target (the boss in its own Pneuma). `Owner` says whose: `self` (default: Blaze Shield's pillars, its own Fire Wall), `party` (a Sage's Land Protector), `monster`, `enemy`, `anyone`. |
| `Count: { Enemy, Who, Around, Range, Below \| AtLeast }` | while that many monsters stand within `Range` cells (default 5) of the companion, or with `Around: target` of the rule's target. `Enemy`: `any` (default), `attacking` (with `Who`, `NotSelf`), `boss`, `slaves`, `casting`. "Three slaves around the boss": `{ Enemy: slaves, Around: target, AtLeast: 3 }` with `Target: { Enemy: boss }`. |
| `Absent: { Ally \| Enemy: ..., ... }` | while a [selector](#choosing-who-selectors) finds **nobody**: `Absent: { Ally: nearest, Job: Priest }` is "no living Priest within sight", the moment to fall back. |
| `Reach: false` / `true` | while the monster the rule is about could not (or could) fight back against the companion where it stands. rAthena teleports a boss hit by someone it can neither hit back from where it stands nor walk to within its chase range; a monster held in place (Ankle Snare, Spider Web) cannot walk at all. `Reach` asks the same question. |
| `Enemy: { Element, Race, Size, Boss }` | while the monster the rule is about (its selector's, or the current target) is one of those: `Element: [Holy, Ghost]`, `Race: Demon`, `Size: Large`, `Boss: true`. Names as rAthena writes them without `ELE_` / `RC_`. For a boss that changes element. |
| `Cooldown:` | when it has not fired in that many ms. |
| `OnePerParty: true` | when no other companion of the party has just fired it at the same target. |

And then does one thing:

| Action | |
|---|---|
| `Cast:` skill, `Level:`, `Target:` | `enemy` (default), `self`, `owner`, `event` (who the event was about), `source` (the monster that caused it), `ally_lowest_hp`, `dead_ally`, or a [selector](#choosing-who-selectors). Ground skills land at the target's feet. Refused where the normal rotation would refuse it: SP, range, weapon, state. |
| `Consume: true` (with `Cast`) | Marks a cast that should pay its catalyst (a Flame Stone, a Blue Gemstone) as a player does. **Not paid yet:** companions have no inventory of their own, so for now the cast goes ahead as if the catalyst were paid, as the engine does for every companion. Once inventories exist, the same rule checks the inventory before casting and pays when the cast starts; tables written today need no change. |
| `Retreat: away` / `owner`, `Distance:` | Steps that many cells away from the monster (or from an event's `source`), or walks back to the owner. |
| `MoveTo: event` | Walks next to whoever the event is about: the companion that sent a `signal`, the member who spoke in party chat. Already beside them: the rule passes. |
| `MoveTo: reachable` | Walks to the nearest cell (within 8) from which the monster could fight back, so hitting it from there does not make it teleport. Already on one: the rule passes. |
| `MoveTo: event_cell` | Walks to where an `On: casts` spell will land, while it is still being cast: onto a party Land Protector before it is down. |
| `MoveTo: { Field, Owner, Within }` | Walks onto the nearest cell of that ground field within `Within` cells (default 8). Already standing on one: the rule passes. |
| `Leave: { Field, Owner, Within }` | Standing on a ground unit placed by `Owner` (default `enemy`: anyone outside the party, monsters included): walks to the nearest free cell within `Within` (default 8). `Field` narrows it to one skill; without it, any unit counts. Not standing on one: the rule passes. `Leave: true` is the same with every default. |
| `KeepDistance: n` | Closer than `n` cells to the monster: walks to the nearest open cell at least `n` away. Already that far: the rule passes, and the next rule (a cast) runs. |
| `Hold: true` | Stands still, without chasing or walking to the target. Without it, a turn no rule took is an ordinary turn, and an ordinary turn walks up to the target. |
| `Say:` text, `Channel: party` / `area` | Speaks. `{name}` `{owner}` `{target}` `{ally}` `{skill}` `{hp}` are filled in. A `Say` rule without an event waits 10 s between lines unless it has a `Cooldown`. |
| `SetTarget: true` | Makes the rule's monster (a selector's, or `source`) the companion's combat target, held for 3 s and renewed while the rule applies. Alone, it does not end the turn. |
| `Switch:` strategy | Makes another strategy of the same plan active. |
| `Signal:` name | Tells the party's other companions, who react with `On: { Event: signal, Name }`. A signal rule without an event waits 5 s between sends unless it has a `Cooldown`. |

A companion that cannot move (petrified, frozen, stunned: whatever rAthena's
`unit_can_move` refuses) skips every movement rule; it does not walk away while
turned to stone.

`Cast`, `Retreat`, `KeepDistance`, `MoveTo`, `Leave` and `Hold` end the companion's turn; only one
of them is allowed per rule. `Say`, `Switch` and `Signal` do not end it and can
come with any of them, after it has succeeded. When no rule acts, the companion takes its
ordinary turn: heals, buffs and the skill rotation (minus anything `Ban` or
`Rotation` takes away). The built-in Party Resurrection comes before all rules:
a dead party member is revived first.

**The normal skill rotation is off under a plan about a monster.** A plan for
`Mob: PHREEONI` (or its encounter) says what to cast, and the companion casts
that and plain-attacks, nothing else from its class's rotation. `Mob: All` plans
are general behaviour and leave the rotation on. Either default can be
overridden with `Rotation: true` or `false` on the job entry. The built-in heals,
buffs and resurrection are not part of the rotation and keep running.

A caster under such a plan still takes ordinary turns whenever no rule acts, and
an ordinary turn walks up to its target and hits it. End a caster's rules with
the lowest-priority `Hold: true`: with nothing to cast, it stands. Its other rules
outrank it and still fire.

### Choosing who: selectors

A `Target` written as a map lets the rule pick its own monster or party member.
The choice is deterministic: the best match by the pick (preferred first, lowest
HP first), then the nearest, then the lowest id. Only those within the cast's
range are considered (`Range` overrides; without a cast it is 14 cells). A rule
whose selector finds nobody does not apply.

| Selector | Picks |
|---|---|
| `{ Enemy: attacking, Who, NotSelf, Prefer }` | a monster attacking `Who` (`party` by default; `owner`, `self`, `tank`, `support`, `attacker`, `any`). `NotSelf: true` leaves out the ones attacking the companion itself; `Prefer` puts those on one member first. |
| `{ Enemy: target_of, Who }` | the monster `Who` is fighting (`owner` by default): assisting. |
| `{ Enemy: nearest \| lowest_hp \| boss \| slaves \| casting }` | the nearest, the most hurt, a boss, a summoned slave, one that is casting. |
| `{ Ally: lowest_hp \| nearest \| missing \| having, Role, Job, Status, NotSelf }` | a party member (the companion included unless `NotSelf`): the most hurt below 100 %, the nearest, the nearest lacking `Status`, or the nearest with it (Status Recovery on the petrified); only those with that `Role` or `Job` (its own or base class). |

With an `Enemy` selector, `When`'s `enemy_*` tokens ask about the chosen monster,
so `not_enemy_provoke` means "that one is not provoked yet". With an `Ally`
selector, `ally_*` tokens ask about the chosen member.

A tank that peels:

```yaml
- Name: peel
  Priority: 80
  Requires: { Role: tank }
  Cast: SM_PROVOKE
  Target: { Enemy: attacking, Who: party, NotSelf: true, Prefer: support }
  When: not_enemy_provoke
  SetTarget: true
  OnePerParty: true
```

Provoke fails on status-immune monsters, bosses among them, and on Undead.

### Regular shells

The AI characters walking the world pick their skills from a rotation too, and
cast whatever comes next at whatever they fight. A plan marked `For: shells` is
theirs (`For: all`: theirs and companions'; `For: companions` is the default):

```yaml
- Mob: All
  Jobs:
    - Job: Wizard
      Build: shells_aoe           # a Build of its own, apart from the companions' Wizard plan
      For: shells
      Start: single
      Strategies:
        - Name: single            # one monster: no area spells
          Ban: [WZ_STORMGUST, WZ_METEOR, WZ_VERMILION, WZ_HEAVENDRIVE]
          Rules:
            - { Name: pack, Count: { Around: target, Range: 4, AtLeast: 3 }, Switch: pack }
        - Name: pack
          Rules:
            - { Name: no_pack, Count: { Around: target, Range: 4, Below: 3 }, Switch: single }
```

What differs for them:
- They have no owner, so rules about the owner (`Target: owner`,
  `Retreat: owner`, `master_*`, `owner_hp_below`) never apply.
- Their party is the synthetic one every shell on a map shares: for them, party
  members are the shells of it within sight, and a `Signal` reaches every shell
  of the map's crowd.
- `Targeting` (Priority, Ignore, MaxAttackers) and holding position against
  following are companion things; regular shells choose targets the way they
  always did, and a rule's `SetTarget` changes the current one.
- Trace one by typing its name and `trace` in your party chat while it is in
  sight; the trace comes to you.

The ambient crowd only takes combat turns while a player has it in view, but that
is still dozens of shells on a busy map: keep their plans short.

### Holding position

A companion normally follows its owner: once it is more than a few cells away,
it walks back, and when idle it takes its place in the formation around the
owner. A rule that positions it (`Hold`, `MoveTo`, `KeepDistance`, `Retreat`,
`Leave`, or standing where a `MoveTo` wants it) holds it there for 0.6 s,
renewed every turn the rule still applies. While it holds, following leaves it
where it is. When no rule holds it any more, it follows again within a turn.

The warps are never held back. A companion still follows its owner to another
map, and is still pulled back once the owner is out of sight.

### Combos

Chain Combo, Combo Finish, Glacier Fist, Chain Crush and the Taekwon kicks are
cast inside the previous step's after-cast delay, as a player does. rAthena checks
the order itself, so list the steps **last first**: a step out of order is
refused and the next rule is tried in the same turn. A combo Monk wants
`Rotation: false`, because a combo starts from a plain hit (Triple Attack).

## Strategies: a state machine per plan

Each plan is a small state machine. `Strategies` are the states, `Start` is
the first, and `Switch` moves between them. Rules outside any strategy apply in
all of them. Names are yours: `approach`, `defend`, `defend_earthquake`.

A strategy can also limit the skill rotation while it is active, with its own
`Ban` (added to the plan's) and `Rotation` (overriding the plan's). That is how a
companion answers a boss that reflects magic:

```yaml
      - Job: Wizard
        Start: normal
        Strategies:
          - Name: normal
            Rules:
              - { Name: mirror_up, When: enemy_magicmirror, Switch: mirrored }
          - Name: mirrored            # no spells while it reflects them
            Rotation: false
            Rules:
              - { Name: mirror_down, When: not_enemy_magicmirror, Switch: normal }
```

A monster's plan starts over in `Start` with every new monster of that kind.
A `Mob: All` plan keeps its strategy until a rule switches it. A `Switch` takes
effect in the same turn: the companion starts again from the top with the new
strategy's rules (at most three switches a turn, so two rules switching back and
forth cannot hang it).

```yaml
        Start: approach
        Strategies:
          - Name: approach
            Rules:
              - { Name: charge, When: self_spheres_lt5, Cast: MO_CALLSPIRITS }
              - { Name: engage, When: enemy_distance_le2, Switch: fight }
          - Name: fight
            Rules:
              - { Name: investigate, When: self_spheres_ge1, Cast: MO_INVESTIGATE }
```

## Events

| `On:` | Fires once when... | `event` is |
|---|---|---|
| `casts` `{ By, Skill, At }` | someone starts casting (that skill). `By`: `monster` (default), `party` (the companion included), `self`, `enemy`, `anyone`. `At`: who it is aimed at, `party` (default for monsters and enemies), `self`, `owner`, `anyone` (default otherwise). Ground spells count as aimed at whoever stands within 3 cells. A cast at the caster itself (a summon, Power Up, a heal) passes the default `At`. `monster_casts` is `casts` with `By: monster`. | who it is cast at; `source` is the caster; `MoveTo: event_cell` is where it lands |
| `encounter_ended` `{ Mob, Reason }` | an encounter monster that was near is not any more. `Reason: died` (dead or removed), `vanished` (alive but teleported, out of sight or on another map), or `any`. Its own plan has stopped applying by then, so put the rule under `Mob: All`. | the monster |
| `target_lost` `{ Reason }` | the companion's target is gone the same ways. Switching to another target does not count. | the monster |
| `signal` `{ Name, From }` | another companion of the party sends `Signal: Name`. `From: anyone` also hears its own. | who sent it |
| `party_chat` `{ Match, From }` | a party member's line contains `Match` (any case). `From: anyone` (default), `owner` or `leader`. | who said it |
| `party_member_died` | a party member on the map dies. | who died |
| `hp_below` / `owner_hp_below` `{ Value }` | the companion's, or its owner's, HP drops below `Value` %. | the companion / the owner |
| `weight_above` `{ Value }` | its weight goes over `Value` %. | the companion |
| `equip_broken` `{ Slot }` | something it wears breaks. `Slot`: `weapon`, `shield`, `armor`, `garment`, `shoes`, `head_top/mid/low`, `accessory_left/right`, `any`. | the companion |
| `item_below` `{ Item, Value }` | it carries fewer than `Value` of an item. Companions have no inventory of their own yet, so this is useful only later. | the companion |
| `status_gained` `{ Status }` | it gets a status. | the companion |

Only skills with a cast time can be seen coming: an instant skill has landed
before anything could react.

### When the boss calls its slaves

Phreeoni's summon (`NPC_SUMMONSLAVE`) has a 0.7 s cast. A Wizard can start its
AoE as the summon starts, on the boss, where the slaves appear:

```yaml
- Mob: PHREEONI
  Jobs:
    - Job: Wizard
      Rules:
        - Name: aoe_on_summon
          Priority: 60
          On: { Event: casts, Skill: NPC_SUMMONSLAVE, Within: 4000 }
          Cast: WZ_STORMGUST
          Target: source          # a ground spell lands at the caster's feet
```

### Gathering on a signal

One companion watches, the others come to it. A Sage that sees a monster begin
a Storm Gust tells the party and lays Land Protector at its own feet; its 5 s
cast is the time the others have to arrive:

```yaml
- Mob: All
  Jobs:
    - Job: Sage
      Rules:
        - Name: lp_for_the_group
          Priority: 90
          On: { Event: casts, Skill: WZ_STORMGUST }
          Cast: SA_LANDPROTECTOR
          Target: self
          Signal: on_me
          Say: "On me!"
    - Job: All
      Rules:
        - Name: gather
          Priority: 88
          On: { Event: signal, Name: on_me }
          MoveTo: event              # next to the Sage; holds there while it applies
```

The signal goes out only once the Land Protector cast has started, so nobody
walks to a Sage who could not cast it.

### Not making a boss teleport

Most bosses teleport away when hit by someone they cannot fight back against. A
companion can check before it attacks, and step to where the boss could reach it:

```yaml
- Mob: All
  Jobs:
    - Job: All
      Rules:
        - Name: no_rude_attack
          Priority: 98
          Enemy: { Boss: true }
          Reach: false
          MoveTo: reachable
        - Name: no_rude_attack_hold   # nowhere it could reach: do not hit it at all
          Priority: 97
          Enemy: { Boss: true }
          Reach: false
          Hold: true
```

### Standing on a party member's Land Protector

```yaml
- Mob: All
  Jobs:
    - Job: Wizard
      Rules:
        - Name: lp_incoming          # the Sage is still casting: go where it will land
          Priority: 85
          On: { Event: casts, By: party, Skill: SA_LANDPROTECTOR }
          MoveTo: event_cell
        - Name: onto_lp              # it is down: get onto it, and stay
          Priority: 84
          MoveTo: { Field: SA_LANDPROTECTOR, Owner: party, Within: 8 }
```

Land Protector also stops ground skills inside it, the companion's own
included. A rule for Safety Wall or Blaze Shield can check
`Field: { Skill: SA_LANDPROTECTOR, Owner: anyone, Range: 0, Below: 1 }` first.
Standing on it counts as holding position (below), so the Wizard stays while
its owner moves about on the same screen.

## Targeting

`Targeting` on a monster changes which monster a companion takes on, never
whether it fights:

- `Priority: n` takes it before lower-priority monsters already in the party's
  fight (in Attack mode, any monster within 12 cells of the owner).
- `Ignore: true` leaves it alone unless the owner fights it or it attacks the
  party.
- `MaxAttackers: n` puts at most `n` of the party on it: the owner counts, then
  companions in a fixed order (lower ids first), and the rest take another
  monster or wait. For bosses that answer a crowd with an AoE (`attackpcge`).
  rAthena counts every unit targeting the boss; this counts the party.

Passive companions are never affected.

## More than one mod

The app combines every enabled mod's table into one, in mod order. A later mod
adds to what an earlier one said:

| A later entry... | |
|---|---|
| with a rule whose `Name` exists | replaces that rule |
| with a rule `Name: x, Remove: true` | deletes rule `x` |
| with new rules, strategies, `Ban` skills | adds them |
| with `Start`, `Rotation`, `Targeting` fields | changes only those |
| with `Reset: true` | starts that monster/job/build over |
| with `Remove: true` | deletes that monster/job/build |

Give rules a `Name` so another mod can replace or remove them.

## Finding out what it is doing

In party chat, the owner types the companion's name and `trace`:

    Seraphina trace

The companion then reports to its owner each rule it acts on, each event it
notices, each strategy change, and why a matching rule's cast failed (out of
range, not enough SP, no catalyst). The same line again does not repeat for 3 s.
Typing it again turns it off.

The server checks the table when it starts. An unknown monster, job, skill, item
or key, a rule with two actions, or a `Start` or `Switch` naming a strategy that
does not exist is reported with its file and line, and that piece is left out.
The rest still loads.

## What it cannot do yet

- **Anything with items.** Shells and companions have no inventory of their own
  yet; it will be added later. Until then they use no items, switch no gear, and
  pay no catalysts (`Consume` is accepted and waits for that).
  `Requires: { Items }`, `item_below` and `weight_above` load and work, but only
  see what the engine hands a companion.
[docs/COMPANION_STRATEGY_ROADMAP.md](../COMPANION_STRATEGY_ROADMAP.md) lists what
comes next for coordinated boss fights, and the Phreeoni playtest that decides
the order.

- **Read a status's strength:** only whether it is there, and its counter.
- **Fight players.** Rules match monsters, and the arena's player-versus-AI
  fights do not run them.
- **React to instant skills**, or to anything between two turns that undoes
  itself before the next one.
