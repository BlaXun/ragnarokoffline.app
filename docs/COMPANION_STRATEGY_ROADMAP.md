# Companion strategies: roadmap

What companion strategies (`db/population_strategy.yml`,
[docs/mods/companion-strategies.md](mods/companion-strategies.md)) still need
before companions can beat a boss **together** rather than each fighting well
on its own. Written down before building, so each step is judged against the
whole.

The order is deliberate. Items 1 and 2 come first, then a played boss fight
(below), and only then 3, 5 and 6, shaped by what that fight shows. Item 4 is
postponed: it needs companions to have an inventory, which they do not yet
(see [Before item 4: inventories](#before-item-4-inventories)).

| # | Item | Status |
|---|---|---|
| 1 | Holding position wins over following | built, not yet played |
| 2 | Leaving hostile ground (`Leave:`) | built, not yet played |
| 3 | Choosing who to help or fight | built, not yet played |
| 4 | Items and gear | **postponed** until shells and companions have an inventory |
| 5 | Time and memory | open |
| 6 | Companions coordinating | signals built, not yet played; roles and claims open |
| 7 | Boss mechanics (MVP survey) | A to F built, not yet played |
| 8 | AI raid parties: shells fighting an MVP on their own | open, after the playtest |

## 1. Holding position wins over following

**The problem.** Owner-follow and its leash run before the companion's turn
(`pop_companion_follow_owner`). The companion loop also stops an idle
companion's walk and sends it to its formation cell. So `Hold`, `MoveTo`,
`KeepDistance`, `Retreat` and `Leave` lost as soon as the owner walked a few
cells away. Standing on a Land Protector or in a ring of Blaze Shield could not
last.

**What it does.** A rule that positions the companion holds it there for a
moment (`population_strategy_holds_position`). While it holds:

- the leash does not walk it back;
- the idle formation step does not move it;
- the idle stop does not cancel the walk the rule started.

Each positional action (or standing where `MoveTo` wanted it) renews the hold.
When no positional rule applies any more, following resumes within a turn.

**What it does not do.** It never stops the warps: a companion still follows its
owner to another map, and is still pulled back once the owner is out of sight
(`AREA_SIZE + 2`). Holding is for a fight on one screen, not a way to leave a
companion behind.

## 2. Leaving hostile ground

`Leave: { Field, Owner, Within }`. If the companion stands on a ground unit
placed by `Owner` (default `enemy`: anyone outside the party, monsters
included), it walks to the nearest free cell with none. `Field` narrows it to
one skill (Storm Gust, Meteor Storm, a trap); without it, any such unit counts.
Not standing on one: the rule passes.

## 3. Choosing who to help or fight (built)

The case that drives it: **a tank that provokes whatever is hitting someone
else.** Today a rule's `Target` is fixed (`enemy`, `owner`, `event`...), so a
tank can only provoke what it already fights.

**Monster selectors** for `Target`, picked deterministically (closest to the
companion, then lowest id):

```yaml
- Name: peel
  Priority: 80
  Requires: { Role: tank }                      # the party role, set in party chat
  Cast: SM_PROVOKE
  Target: { Enemy: attacking, Who: party, NotSelf: true, Prefer: support }
  When: not_enemy_provoke                       # When's enemy_* is the chosen monster
  SetTarget: true                               # and keep fighting it
  OnePerParty: true                             # two tanks never provoke the same one
```

- `Enemy: attacking` with `Who: owner | party | support | self`; `NotSelf` for
  "hitting someone other than me". It reads each monster's target, which the
  engine already tracks per companion.
- Also `Enemy: nearest | lowest_hp | boss | slaves | casting`.
- With a selector, `When`'s `enemy_*` tokens ask about **the chosen monster**,
  not the current target, so `not_enemy_provoke` checks the right one.

**Ally selectors** for buffs and heals: `Target: { Ally: lowest_hp, Job: Knight }`,
`{ Ally: nearest, Role: tank }`, `{ Ally: missing, Status: SC_BLESSING }`.

**`SetTarget: true`** makes the chosen monster the companion's combat target for
3 s, renewed while the rule keeps applying. It needs no new engine line:
`population_strategy_target` already has the last word over the party
controller's choice, the same way holding position overrides following.
Assisting is a selector: `Target: { Enemy: target_of, Who: tank }` with
`SetTarget: true` takes the tank's target instead of the owner's.

Provoke itself fails on status-immune monsters (bosses, so Phreeoni) and on
Undead, and succeeds by chance otherwise (rAthena's `skills/swordman/provoke.cpp`).
Against Phreeoni, the tank's Provoke is for its slaves.

**`Requires: { Role: tank }`** gates a rule on the party role assigned in chat
(`<name> tank`), so one table serves a party arranged differently each time.
This was listed under 6; it belongs here because peeling is a tank's job.

Range: a monster out of the skill's range is not chosen for a `Cast`, so a tank
provokes what it can reach. If the playtest shows it should walk to one first,
that is an `Approach:` option on the rule.

## 4. Items and gear (postponed)

- `UseItem:` on self or an ally: potions, Yggdrasil Leaf, Fly Wing; with a target
  (a corpse) the server completes the target step a client would send.
- Gear sets per monster: an elemental weapon or armour.

Both wait for inventories (below). Without one, item use either costs nothing,
and so means nothing, or never happens because the bag is always empty.

## 7. Boss mechanics: what the MVPs do that rules could not answer

A survey of every MVP's `mob_skill_db` rows (renewal: 90 MVPs with skills, about
1,950 rows; the conditions are `always` 1054, `myhpltmaxrate` 390, `slavele` 159,
`rudeattacked` 135, `skillused` 85, `longrangeattacked` 34, `attackpcge` 15,
`casttargeted` 12, and a few others). Most boss skills are **instant**, and an
instant skill cannot be seen coming. A rule can only answer its *result*: a
status on the boss, a ground field, new monsters. These are what that needed.

| | Gap | What it answers | Status |
|---|---|---|---|
| A | `Ban` and `Rotation` per **strategy**, not only per plan | Reflect Shield (14 rows), Magic Mirror (7), Auto Guard, Stone Skin (11), a boss in its own Pneuma (14) or Safety Wall (6): "no magic / no melee / no ranged until it drops" is a strategy whose rotation is limited | built |
| B | `Field: { ..., At: target }`: ground units around the rule's target | the boss standing in its own Pneuma, Safety Wall or Land Protector (16) | built |
| C | `Enemy: { Element, Race, Size, Boss }` on a rule | bosses that change element (NPC_CHANGEHOLY, CHANGETELEKINESIS...); `When` cannot express element or race | built |
| D | **Counting** monsters around a point (D1), and a cap on how many companions take one target (D2) | instant Call Slave (152 rows): "3 slaves around the boss → AoE"; `attackpcge` (15): bosses that answer N attackers with an AoE | built: `Count:` and `Targeting: { MaxAttackers }`. rAthena's `attackpcge` counts every unit targeting the boss; the cap counts the owner and the party's companions, lower companion ids first |
| E | **Can the boss reach me?** A path check before attacking from range | `rudeattacked` → Teleport, **135 rows, the commonest boss reaction**: hitting a boss from where it cannot walk to makes it vanish. rAthena decides it in `mob.cpp` (can it hit back from where it stands; can it move; `unit_can_reach_bl` within its chase range), so a rule can ask the same question. Holding a boss in place (Ankle Snare, Spider Web) counts as "cannot reach back" too | built: `Reach: false` on a rule, and `MoveTo: reachable` |
| F | **Encounter ended / target lost** events | after a Teleport the encounter plan just stops applying: "it teleported, regroup on the owner" | built (`encounter_ended`, `target_lost`, each with `Reason: died \| vanished`) |

Not answerable: an instant skill before it lands (Teleport, Call Slave, instant
summons, Power Up, Heal, instant Meteor / Land Protector / Heaven's Drive /
Pneuma, Dispel, Full Strip). Rules answer what follows: the status
(`enemy_*`, `Ally: having`, `Ally: missing` to rebuff after Dispel), the field
(`Field`, `Leave`), the monsters (D). Gear stripped or broken (Full Strip, the
breaks) waits for inventories.

Already answerable: the cast-time AoEs (Hell Judgement 30, Earthquake 29, Lord
of Vermilion 26, Meteor 22, Storm Gust 21, the Wide statuses ~60 together) with
`On: casts`; summons with a cast time (151); reactions to our own skills
(`skillused`, `groundattacked`, `casttargeted`) with a plan's `Ban`.

## 8. AI raid parties (open)

Shells fighting an MVP on their own, as a party, with nobody's character in it.

**What exists.** Every ambient shell already belongs to a synthetic party, one per
map (`0x70000000 | map`, `population_engine.cpp`), so party-only skills such as
Kyrie and Devotion work between shells; with `PackBehavior`, idle shells share a
target. The PvP arena spawns teams in synthetic parties of their own
(`population_arena_start`, `npc/custom/population/arena.txt`). So shells fight side
by side, but as "everyone on this map": no leader, no goal, no plan.

**What a raid party needs:**

1. **A group**: a synthetic party per group, spawned by a script command in the
   arena's style. Engine work; a new script command also touches the engine's
   rAthena patch (`custom/script.inc`).
2. **A leader with a goal**: go to the MVP, find it, and the others follow that
   shell. Engine work: owner-follow knows only real players.
3. **Strategies for them**: let a raid group's shells (not ambient ones) run the
   strategy module, and let the module list a synthetic party's members (it asks
   rAthena's party table today, which does not know them). Module only, small.
   The plans themselves carry over unchanged.
4. **Someone watching**: shells only take combat turns while a real player has
   them in view (`pop_combat_tick_per_real_pc`); companions are the exception. A
   raid party would fight while watched, not on an empty map.
5. **A decision on rewards**: an AI party that kills an MVP takes it from players,
   and its MVP item and drops need an inventory (item 4) to go anywhere.

Decide after the Phreeoni playtest, once the strategies are seen holding up with
a real player in the party.

## Before item 4: inventories

Shells and companions have **no inventory of their own** yet. Nothing stocks
one, the owner cannot see or manage it, and it is lost with the shell. What a
companion holds is what the engine hands it: its gear and virtual ammunition.
Inventories will be added later, as their own piece of work, together with an
answer to who stocks them: the owner by trade, a shopping trip, or a virtual
supply like the Blue Gemstones for Resurrection.

Until then:

- **Item use and gear switching** (item 4) are postponed.
- **Catalysts are ignored.** The format already has `Consume: true` and it is
  checked when the table loads, but one switch in the strategy module,
  `kPayCatalysts`, is off. A `Consume` rule therefore casts as if its catalyst
  were paid, which is what the engine does for every shell anyway. Turning the
  switch on with inventories makes every `Consume` rule check the inventory
  before casting and pay when the cast starts. Nothing else changes: tables
  written today keep working.
- **Item-based conditions are inert.** `Requires: { Items }`, `item_below` and
  `weight_above` read the companion's runtime inventory, which holds only what
  the engine gave it. They load and work, but they become useful only with
  inventories.

## 5. Time and memory (open)

- Time in the current strategy and in the fight: `in_strategy_gt10s`, for "every
  30 s it casts X" and phase timers.
- Time left on a status: rebuff before Assumptio or Blessing lapses, not after.
- A few counters or flags per plan (`Set:` / `Inc:` and a condition on them),
  for "Lex was cast on this boss" or "phase 2 started".

## 6. Companions coordinating (open)

- **Built:** `Signal: name`, `On: { Event: signal, Name }` and `MoveTo: event`,
  between companions of one party: "on me", "the tank has it", "I'm out of SP".
  Moved ahead of the playtest because gathering is what boss fights turn on.
- **Built:** role plans for any boss (`Mob: Boss`), in
  `examples/mods/companion-roles`. The class family picks the role and a Duty
  overrides it (`Requires: { Role: [support, none] }`). Boss plans now hold only
  each boss's own mechanics. Rotation is layered: a plan saying `false` wins,
  then one saying `true`, then the default. Taken from the Phreeoni plan; not
  yet played against a second boss.
- **Built:** kinds of monster, `Mob: { Race, Element }`, between a particular
  monster and `Boss`, with `Race`/`Element` on Enemy selectors and `Count`. A
  specific plan can `Disable` a broader plan's rule by name. Examples: Undead
  and Ghost in companion-roles. The layers are, in order: monster, encounter,
  kind, Boss, All, and on every layer, job, family, 1st class, All.
- Beyond `OnePerParty`: claims on targets, so crowd control goes to different
  monsters and the party's Lex Aeterna is not wasted twice.

## Playtest: Phreeoni

The first played boss fight, after 1 and 2: a tank, a Priest and a damage dealer
with Wizard support, traces on (`<name> trace`).

Why Phreeoni. Its `mob_skill_db` (renewal adds All Heal; the rest is the same in
both eras) tests most of what the rules are for:

| Phreeoni does | What it tests |
|---|---|
| **Teleports** when attacked by someone it cannot reach (`rudeattacked`) | ranged companions placed badly lose the boss; positioning (1) |
| **Summons and calls slaves** | targeting: boss or slaves (3, `Targeting: Ignore`) |
| **Wide Stone Curse** below some HP (petrify around itself, 0.5 s cast) | `On: casts` + `KeepDistance`/`Retreat` in time |
| **Petrify Attack**, **Lick**, **Helm Break** | Priest reactions (Status Recovery), gear (4) |
| **Power Up** and **Hiding** below some HP | phases (5); Hiding is the "where did it go" moment |
| **Heal**; **All Heal** in renewal when hit hard | burst timing, focus (3, 5) |
| Renewal: 300,000 HP, defence 269, magic defence 98. Pre-renewal: 188,000 HP, defence 10 | a long fight; SP and consumables (4) |

Land Protector does not help against Phreeoni itself. Its Wide Stone Curse is
a petrify around the boss, not a ground spell, and its Heaven's Drive is instant,
so nothing sees it coming. Signals still matter there: gathering for heals or a
Sanctuary when it powers up, or "it is hiding" when it vanishes.

What to record: each rule that fired and its outcome (the trace), where it broke,
and which open item would have fixed it. That list decides the order of 3, 5
and 6.
