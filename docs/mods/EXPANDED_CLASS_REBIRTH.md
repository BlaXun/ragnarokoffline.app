# A renewal expanded class in pre-renewal, by rebirth

How to bring one of renewal's expanded second classes (Kagerou/Oboro,
Rebellion, ...) to a **pre-renewal** server as a mod, reached the way a
transcendent class is: by rebirth. It is written for an AI agent doing the
work, and says where the person it works for has to decide or check
something.

Every class, expanded or third, lives in one mod,
[`registry/mods/transcendent-third-classes`](../../registry/mods/transcendent-third-classes),
with one generator script,
[`registry/tools/transcendent-third-classes/build.py`](../../registry/tools/transcendent-third-classes/build.py),
holding a config per class. The worked example is the Kagerou and Oboro
(`npc/kagerou_oboro.txt`, `lua/kagerou_oboro.lua`, the `kagerou_oboro` config
and its CSVs in `kagerou_oboro/`); they were a mod of their own at first.
Read those before starting. Most of what follows is what they ran into.

---

## 0. The shape of the work

The result is **a class added to the one registry mod, era `pre-renewal`**,
that changes nothing in rAthena, the population engine or the app. rAthena already compiles every
expanded class and its skills into a pre-renewal build. What pre-renewal lacks
is data, and data is what a mod ships:

| Missing in pre-renewal | Supplied by the mod |
|---|---|
| the class's HP, SP, EXP, ASPD, job bonuses, weight | `db/job_stats.yml` |
| its skill tree | `db/skill_tree.yml` |
| current skill definitions (pre-re's are an old revision) | `db/skill_db.yml` |
| permission to wear the base class's gear and ammo | `db/item_db.yml` |
| a way to become one | `npc/` (a rebirth and job-change NPC) |
| balanced skill damage | `lua/` ratio hooks, plus `db/skill_db.yml` for what Lua cannot reach |
| class gear at pre-re levels | `db/item_db.yml`, `db/item_combos.yml`, `db/mob_db.yml`, `System/itemInfo.lua` |
| consumables pre-re has no source for | a shop in `npc/` |

Everything under `db/` and `System/` is **generated** by
`registry/tools/transcendent-third-classes/build.py` (a config per class),
from the pinned rAthena plus each class's CSV files, in a directory of its
own beside the script, that a person edits. The NPC and the Lua are written by hand. The generator never ships with
the mod.

If you find yourself wanting to edit rAthena, stop and ask: the point of this
recipe is that it does not need to.

---

## 1. Decisions the human makes first

Ask these before writing anything. Each has a default from the Kagerou mod;
offer it, but let the person choose.

1. **The path.** Default: base class 99/70 → reborn as a plain Novice →
   Novice job 10 → base class again → expanded class from base-class job 50.
2. **Power target.** Damage was first set "a little below the transcendent
   classes". Since 2026-10 the rebirth classes follow the third classes'
   rules (§12): 0.85-1.0 of a transcendent class on one target, and a
   fighter's area damage per target at about half of its own single target
   (casters exempt). Agree **which transcendent class to compare against**
   (melee: Assassin Cross; ranged: Sniper; caster: High Wizard), and every
   build the class supports (the Kagerou fights, the Oboro casts too).
3. **Max job level of the expanded class.** Default 60 (see §4 for why).
4. **Rebirth stat points.** Default: the transcendent 100, given as +52 when
   the character becomes the base class again (see §5 for why then).
5. **Gear.** How it is obtained (Kagerou: monster drops), how much (Kagerou:
   a full set per tier, four tiers, levels 50-95), and from which monsters.
   Propose themed monsters and rates. The person signs them off.
6. **Names and flavour.** The NPC names, item names and descriptions are
   creative choices. Propose them, and expect to be corrected.

Write the agreed decisions to memory as you get them. They are what a later
session needs.

---

## 2. Find out what pre-renewal has

Do this against the rAthena commit `config/VENDOR_PINS` pins, not a fork
checkout's HEAD. Read files with `git show <pin>:<path>` from a checkout that
has the commit.

```bash
PIN=$(awk '$1=="rathena"{print $3}' config/VENDOR_PINS)
R=../rathena                       # any checkout containing $PIN
show() { git -C $R show $PIN:$1; }
CLASS=Rebellion                    # the Jobs: key, e.g. Kagerou

# 1. The job tables: expect 0 in pre-re and a count in re
for f in job_stats job_exp job_basepoints job_aspd skill_tree; do
  echo "$f pre:$(show db/pre-re/$f.yml | grep -c $CLASS) re:$(show db/re/$f.yml | grep -c $CLASS)"
done

# 2. The skills: pre-re has entries, but are they the same revision?
#    Diff every <PREFIX>_ skill (KO_/OB_/KG_, RL_, ...) between eras, and list
#    which renewal entries carry a Status: line.

# 3. The C++: the class and its skill classes exist whatever the era
grep -rn "JOB_$(echo $CLASS | tr a-z A-Z)" $R/src/common/mmo.hpp
ls $R/src/map/skills/<base class folder>/
grep -n "#ifdef RENEWAL" $R/src/map/skills/<folder>/*.cpp   # era-split formulas
```

Things the Kagerou mod found this way, and you should expect again:

- **`@jobchange <id>` fails silently** in stock pre-re ("You are unable to
  change your job.", nothing in map.log). That is `pc_jobchange` →
  `job_db.exists()`: there is no job_stats entry. It is the first thing the
  mod fixes.
- **Pre-re's skill entries are an older revision.** In pre-re all 18 changed
  Kagerou skills had no `Status:` line. The generic code starts
  `skill_get_sc(skill_id)`, so every buff started *nothing*. Some also had
  different target types (Ground against Attack) from what the skill classes
  in `src/map/skills/` handle now. The 17 Rebellion `RL_` skills that differ
  look the same. **Ship renewal's entries.**
- **Class-specific checks in `skill.cpp`.** Search the skill names in
  `src/map/skill.cpp` `skill_check_condition_castbegin`. Cross Slash
  (`KO_JYUMONJIKIRI`) fails unless the caster holds a weapon in both hands.
  That is stock behaviour, but it decides how you test it and what the README
  says.
- **Damage added outside the ratio.** Search `battle.cpp` for
  `case <SKILL>:`. Kunai Splash adds `3 × (base ATK + weapon ATK + ammo ATK)`
  with `ATK_ADD`, which a Lua `ratio` hook cannot scale (see §7).
- **Consumables.** List every `ItemCost:` and `Ammo:` in renewal's skill
  entries, then search pre-re's NPCs and mob drops for each item. Renewal
  sells Kagerou's charms through a barter shop pre-re lacks, so the mod sells
  them.
- **Items that don't exist in pre-re at all.** Rebellion's skills consume
  four renewal-only items (Full Metal Jacket, mines, Dragon Tail Missile, Slug
  Bullet) and Platinum Alter *requires* two renewal-only bullets as equipment.
  Copy those entries from renewal's item tables under their own ids, which
  the client already knows, with the new class's job flag. **One missing
  item named in a skill's `Requires:` makes rAthena reject the whole skill
  entry** (`Requires Equipment … does not exist`), so the generator checks
  every item a shipped skill entry names.
- **The job-change quest** lives under `npc/re/jobs/2e/` and is loaded only in
  renewal. Don't port it. The rebirth NPC replaces it.

---

## 3. How the import layer behaves

These rules decide what the generator must write. Several of them fail
silently.

- **`db/import/job_stats.yml` holds everything.** There is one `JobDatabase`
  (`pc.cpp`), and its imports are `job_stats.yml` only. Stats, `BaseASPD`,
  `MaxBaseLevel`/`BaseExp`, `MaxJobLevel`/`JobExp` and `BaseHp`/`BaseSp` all
  go in that one file, in one entry per job group. There are no import stubs
  for `job_exp`, `job_basepoints` or `job_aspd`.
- **Header versions**: copy them from `db/import-tmpl/<file>` at the pin
  (JOB_STATS 4, SKILL_TREE_DB 1, SKILL_DB 4, ITEM_DB 3, MOB_DB 5, COMBO_DB 1).
  An old version still loads, in a "reduced compatibility" mode with a
  warning.
- **A `skill_db` import entry only replaces the fields it names.** If pre-re
  sets a field that renewal's entry leaves out, pre-re's value survives. For
  Kagerou that was Cross Slash's `AfterCastActDelay: 500` and Rapid Throw's
  `Duration1`. The generator diffs the top-level keys and writes an explicit
  reset for each one: `0`, `Range: 0`, `Element: Neutral` (rAthena's defaults
  when the key is absent). It also fails on a key it has no reset value for,
  rather than guessing.
- **Maps inside an entry merge key by key, too.** `DamageFlags`, `Flags` and
  the `Requires` maps `Ammo` and `Weapon` only set or clear the keys an import
  names. Rebellion's Dragon Tail kept pre-re's `DamageFlags: NoDamage: true`
  this way: `skill_get_casttype` then returned `CAST_NODAMAGE`, and the skill
  spent its missile and hit nothing, with no error anywhere. It also kept
  pre-re's grenade-ammo requirement. The generator writes `Key: false` for
  each leftover flag, `Ammo: None: true` or `Weapon: All: true` to clear a
  leftover requirement, and fails on leftovers in `Equipment`, `State` or
  `Status`, which have no clearing key.
- **An item import entry's `Jobs:` replaces the whole list.** To add the new
  class to an item, restate every job already on it plus the new flag
  (`KagerouOboro: true`, `Rebellion: true`; the names come from rAthena's
  `EAJ_` constants).
- **Scan all three item files**: `item_db_equip.yml`, **`item_db_etc.yml`**
  (ammo: kunai, shuriken, bullets) and `item_db_usable.yml` (class potions).
  The first version only scanned equipment, and Kagerou could not equip a
  single kunai.
- **`Drops:` without `Index:` is appended,** up to ten per monster. The
  generator counts the stock drops and fails if a monster would go over ten.
  Pre-re monsters usually have eight, so two new drops fit. **MVPs count
  too**: their `Drops:` list has eight entries as well, so check them the
  same way. **Two class mods must not share a monster**: each adds two drops,
  and together they pass ten. Rebellion's monsters were chosen to avoid
  Kagerou's.
- **Item ids** for mods: 50000-99999. Pick a block in the middle.
- **`System/itemInfo.lua` is additive.** Ship only your items. The app lists
  it ahead of the client's own table.
  - Borrow art by copying a stock item's `identifiedResourceName` /
    `unidentifiedResourceName` and `ClassNum` from the translation's table
    (`vendor/ROenglishRE/.../LuaFiles514/itemInfo.lua`). **That file is
    cp949** with a few stray bytes: decode with `errors="replace"`, and fail
    if a name you use came out with U+FFFD in it. Write yours as UTF-8.
  - For headgear, copy the stock item's `View:` **and** its `Locations:`. The
    view has to match the slots, or nothing draws. Kitsune Mask is
    `Head_Top`, Assassin Mask `Head_Low`, Kabuki Mask all three.

---

## 4. The numbers

### Skill points

With `player_skillup_limit: yes` (the stock setting),
`pc_calc_skilltree_normalize_job` (`pc.cpp`) holds a second-class character
in its **first-class** tree until it has *learned* (not merely owns)
`9 + (change_level_2nd − 1)` skill levels. `change_level_2nd` is the job level
the character had when it became the second class (`pc_jobchange`).
Consequences:

- **Saving points gains nothing.** A Ninja who changes at job 70 with 69
  unspent points can learn only Ninja skills until all 69 are spent. This was
  verified in game.
- **Extra base-class job levels add base-class skill points, not
  expanded-class ones.** The expanded class's own budget is always
  `MaxJobLevel − 1`.
- The renewal tree **inherits** the base class (`Inherit: Ninja: true`), so
  points earned as the expanded class can still go into base-class skills.

Renewal's expanded classes go to job 70 (`db/re/job_exp.yml`), so renewal's
total is `9 + 69 + 69 = 147` and its own skills get 69 points. With the change
opening at base-class job 50 and a max job of 60, the total here is
`9 + (J − 1) + 59`: 117 at job 50, 127 at job 60 (a transcendent class's total
of 9 + 49 + 69), 137 at job 70. That is always ten below renewal for the same
change level, and the class's own skills get 59 points against renewal's 69:
"a little below" in skill points as well as in damage. The base class needs no
upper cap, which no NPC could enforce anyway. A max job of 70 would give
exactly renewal's numbers, if the person wants the class on par.

### job_stats

Derive it from stock tables, so a reviewer can follow the arithmetic. In the
generator these are named constants at the top:

| Field | Kagerou's choice | Why |
|---|---|---|
| BaseExp | the transcendent table (`Assassin_Cross`'s group) | a rebirth class levels like one |
| JobExp | the transcendent second-job table, cut at MaxJobLevel | |
| BaseHp | the 2-1 class's table × 1.1 (Assassin) | a transcendent class gets × 1.25 from its upper flag; the new class has no upper flag |
| BaseSp | the base class's table × 1.1 | |
| BonusStats | renewal's to its last level, then a few more to the max job | +40 against a transcendent class's +45 |
| BaseASPD | the base class's pre-re values | renewal's use another scale (40/45/50 against 400/500/750) |
| MaxWeight | the base class's | |

Check the caps in game: `@joblvl 100` must stop at the max job, and
`@blvl 200` at 99.

---

## 5. The NPC

Mirror stock rebirth (`npc/jobs/valkyrie.txt`). One NPC, next to the base
class's job master, with a character variable for the path
(`<mod>_reborn`: 1 reborn, 2 base class again, 3 done):

1. **Base class 99/70 → Novice.** Require `Weight == 0`, `Zeny == 0` and
   `SkillPoint == 0`, like the Valkyrie. Then: `F_ClearJobVar`,
   `jobchange Job_Novice`, `resetlvl(1)`, **`StatusPoint = 48`**, First Aid
   and Play Dead as `SKILL_PERM`, Knife_ and Cotton_Shirt_.
   - Use `Job_Novice`, not `Job_Novice_High`. The base class has no upper
     version, and a High Novice changing at any stock NPC would turn into a
     transcendent first class.
   - `resetlvl(1)` sets 100 status points only for `JOB_NOVICE_HIGH`. For a
     plain Novice it leaves whatever the character had, so set them yourself.
2. **Novice job 10, `NV_BASIC` 9 → base class**, plus **`StatusPoint += 52`**.
   Give the transcendent bonus here, not at rebirth. A reborn Novice who walks
   off to another class's job NPC would otherwise keep 100 points as an
   ordinary class.
3. **Base class job ≥ 50, `SkillPoint == 0` → expanded class**, by sex where
   the class is split (`Job_Kagerou`/`Job_Oboro`). Say how many more
   **base-class** points waiting longer would give. The first version said
   "more points as a Kagerou", which was wrong: see §4.

Put the requirements in the dialogue before the confirmation, and refuse with
a reason. If the skills need consumables pre-re cannot otherwise get, add a
shop: a script NPC that checks the class and calls `callshop` on a hidden
`shop`.

---

## 6. Gear

Data a person edits, so it lives in CSV beside the generator:

- `equipment.csv`: id, aegis, name, tier, kind, level, ATK/DEF, weapon level,
  slots, weight, borrowed look, item script, description lines
- `drops.csv`: mob aegis, item aegis, rate (0.01% units)
- `combos.csv`: tier, items, script, description

The generator checks that:
- every look is a pre-re item with art in the translation table;
- every equipment item drops from at least one monster;
- no monster goes over ten drops;
- no id collides with a stock item.

It writes the set bonus into each piece's description. Write descriptions in
the translation's style: flavour line, rule, bonuses, rule, then Type,
Attack/Defense, Weight, Level, rule, Requirement. Skill names must match
`skill_db`'s `Description:`.

For stat levels, read pre-re's own items of the same type and level (for
example Huuma Blaze, ATK 185 at level 55; Ginnungagap, 148 at 70). Stay a step
below the best of them, since the class-only bonuses (`bSkillAtk`) add to
that.

---

## 7. Balance: measure, don't estimate

Estimates from the formulas were wrong in both directions. The first Lua
factors were set from paper:
- Cross Slash came out *above* Sonic Blow.
- Swirling Petal came out at a third of Meteor Assault.
- Kunai Splash, which looked harmless on paper, came out at four times Sonic
  Blow.

Only measuring found these.

### Tools

- **Lua `ratio` hook** (`skill("NAME", { ratio = function(c, stock) return stock * f // 100 end })`).
  It scales the skill's whole percentage, including what the class adds (the
  Cross Slash mark, Kagemusya). Use it for anything computed through
  `calculateSkillRatio`.
- **`db/skill_db.yml` fields** (`AfterCastActDelay`, `Cooldown`, costs) for
  anything that adds damage with `ATK_ADD` in `battle.cpp`, which a ratio
  cannot reach. Kunai Splash got Sonic Blow's 2 s delay; Tiger Cannon,
  whose damage comes from HP and SP, a 7 s cooldown. A field the entry
  lacks (Gates of Hell had no Cooldown) is added. Put such overrides
  in a named table in the generator (`SKILL_OVERRIDES`), with a comment saying
  why, and mark the line in the output.
- Leave era-independent skills alone: zeny-based (Rapid Throw), %-of-HP
  (Illusion – Death), pure buffs and debuffs.

### The fixed cast time rule

Renewal splits a skill's cast into a variable part, which DEX reduces, and a
**fixed** part, which it does not. Pre-renewal has only the first: every cast
time is `cast × (1 − DEX / 150)` (`castrate_dex_scale`), and rAthena honours
`FixedCastTime` only when the global `RENEWAL_CAST` flag is compiled in. A
renewal skill copied as it is therefore loses its fixed part, and at high DEX
it fires almost instantly: Soul Reaper's Espa (0.5 s cast + 1 s fixed in
renewal) cast in a quarter of a second and chained every 0.6 s, at 30 times
a High Wizard's damage per second. No damage factor fixes how that plays.

The rule, decided with the mod owner and applied to every class mod:

- **75% of each skill's renewal `FixedCastTime` is added to its
  `AfterCastActDelay`, and the other 25% to its `CastTime`.** `FixedCastTime`
  is set to 0. After-cast delay is pre-renewal's own limiter (Sonic Blow, the
  bolts and Storm Gust are held back by it) and DEX does not reduce it, so it
  puts a floor under the skill's rate; the 25% keeps a short, interruptible
  cast bar so the skill still feels cast. Espa becomes a 0.75 s cast (before
  DEX) and a 0.75 s delay.
- **Exception: a skill, or a level of one, with a cooldown of 10 s or more
  keeps its whole fixed cast as cast time.** Its cooldown already stops spam,
  and as cast time it can be reduced the way renewal reduced fixed cast: by
  DEX, and by Kagerou/Oboro's Izayoi, which in pre-renewal halves the whole
  cast (`skill_castfix_sc`, `#ifndef RENEWAL_CAST`) but never touches delay.
  Distorted Crescent goes from 3.9 s of lockout at DEX 90 to 3.0 s, and 2.0 s
  with Izayoi; Soul Unity from level 2, Soul Explosion, Nova Explosion and
  the Soul Reaper buff are the others.
- In the generator: `FIXED_CAST_TO_DELAY=0.75` and
  `FIXED_CAST_COOLDOWN_EXEMPT=10000` (the default) in the class's
  `build.py`. Every converted line is commented in the generated entry.
- **Measure after converting.** The delay slows the skill, so its damage
  factor has to be set from the converted entry: Rebellion's rifle pair fell
  from 0.85 to 0.56 of a Sniper when the rule went on, and its factors went
  up to compensate.

Caveats to tell the owner: Bragi and delay gear (Kiel-D-01 Card) reduce the
delay, as they do for every pre-renewal class; delay comes *after* the hit
where fixed cast came before it, which matters for PvP timing but not for
damage per second; and a combo starter that gains delay may lose its combo
window, so check every combo after converting.

### Method

1. Build both characters from one template: base 99, max job, the same stats
   allocation, `@allskill`, and a test weapon of the same ATK for each class's
   weapon type (a 150-ATK Katar, Dagger, Huuma, ... defined in a *test-only*
   mod).
2. Use one immobile target: a test-only monster with a lot of HP, set DEF
   and VIT (Kagerou used 30/30), `NoRandomWalk`, and a negligible attack.
3. Spam the skill every 0.1 s for 30 s, and total the damage the client
   receives. The server enforces delays and cooldowns itself, so spamming
   gives the real maximum rate. **For skills with a cast bar, also measure
   paced** (one request per cast + delay, and one skill per tick for a
   rotation) and keep the best: requests during a cast cost Jupiter Thunder
   two thirds of its casts.
4. Measure **rotations**, not just single skills. A skill with a cooldown
   (rather than a delay) leaves gaps another skill fills: Cross Slash plus
   Soul Cutter was 1.6 × Sonic Blow while Cross Slash alone was 1.37 ×.
5. Compare single-target skills with the reference's single-target skill, and
   area skills with its area skill.
6. **Clear statuses before every run** (`sc_end SC_ALL`). Buffs from an
   earlier run survive logout. A leftover status made the same skill measure
   1,150 per cast on one character and 3,570 on the other.
7. Set factors as `old × target / measured`, then measure again. Record the
   final table in the Lua file's header and in the README, and the runs
   behind it in a spec beside `build.py` (`balance-<class>.json`, §8), so the
   next person can measure the same thing again.
8. **Ground skills report their damage from their skill unit**, not from the
   caster (the packet's source is the unit's id). Count them by skill id, or
   Storm Gust and Lord of Vermilion read as zero.
9. **Cast toggles and long buffs once, at the start.** Star Emperor's
   Universe Stance is a toggle: re-casting it every 10 s switched it off half
   the time, and every kick measured low until that was found.
10. **Resources set the real rate.** Soul energy comes from Soul Collect at
   one per 20 s (the Soul Reaper buff only gains it from players); Gunslinger
   coins from Rich's Coin. Measure the sustained rotation on the real income,
   and the burst with an unlimited supply (`@soulball`, `@spiritball` in the
   test helper) to check it does not overshoot.
11. **Pick the reference by role**: Assassin Cross for melee (Sonic Blow,
   Meteor Assault), Sniper for ranged (Double Strafe), High Wizard for casters
   (Jupiter Thunder, Cold Bolt; Lord of Vermilion for area).

Kagerou's numbers after the 2026-10 pass (damage per second; area skills per
target, against the Kagerou's own single target):

| Kagerou / Oboro | Compared with | Ratio |
|---|---|---|
| Cross Slash + Soul Cutter: 872 | Sonic Blow: 1,016 | 0.86 |
| Swirling Petal: 440 | its single target: 872 | 0.50 |
| Kunai Splash: 488 | its single target | 0.56 |
| Kunai Explosion: 430 | its single target | 0.49 |
| Ice Spear, Oboro, INT build, ten charms: 3,184 | amplified Jupitel Thunder: 2,234 | 1.43 |
| Ice Spear, Kagerou, INT build, ten charms: 2,810 | amplified Jupitel Thunder | 1.26 |
| the same on a warded dummy: 1,677 / 1,398 | 1,176 | 1.43 / 1.19 |
| Kamaitachi, INT build, ten charms: 2,177 | amplified Meteor Storm: 1,326 | 1.64 |

The magical numbers sit above parity on purpose (the owner's call): the
Ninja's spells are weak, charms are the Kagerou's and Oboro's gain, and
without charms they cast exactly as a Ninja. Only 48% of the charm bonus
is kept (renewal's full bonus put a charged Oboro at 1.8 times a High
Wizard).

A class with more than one build gets a run per build. A magical build may
use skills the mod never changed (the Ninja's spells): measure it anyway,
since the class around them (its buffs, its stats) did change.

**The human decides whether those ratios are right.** Show them the table,
and say what it leaves out:
- buffs on both sides (Kagemusya, Enchant Deadly Poison);
- gear bonuses;
- auto-attacks between skills;
- PvP.

---

## 8. Testing without the app

`scripts/rotest` needs the app, and so macOS. On Linux or WSL, use the
headless rig in `registry/tools/expanded_class/balance/` (its README has the
commands). `setup.sh` builds the pinned rAthena for pre-renewal in Docker,
and `run_specs.py <mod's balance.json>` loads the mod, measures every run
and checks each ratio against its aim:

```
registry/tools/expanded_class/balance/setup.sh ../rathena
python3 registry/tools/expanded_class/balance/run_specs.py registry/tools/transcendent-third-classes/balance-kagerou-oboro.json
```

A spec run is one rotation on the §7 template against the test dummy, with
the run it is compared with and the band its ratio should fall in. The
third classes keep their runs in `registry/tools/transcendent-third-classes/balance.json`,
each expanded class in `balance-<class>.json` beside it; when a
factor changes, the spec is run again and the README's table follows it.

What the rig is made of, for when it needs changing:

- **Server.** Build rAthena **at the pin** in Docker, the way
  `containers/rathena/Dockerfile` does: alpine,
  `./configure --enable-packetver=<first line of config/PACKETVERS> --enable-prere`,
  then `make server`.
  - Run MariaDB in a container and import `sql-files/main.sql` and
    `logs.sql`. Replay `main.sql` on every start, since a new pin may add
    tables (`mod_store`).
  - Move every port off the defaults, in case the app is running.
  - Put `enable_ip_rules: no` in `conf/import/packet_conf.txt`. Without it,
    rAthena's DDoS guard blocks localhost after a few quick logins.
- **Installing a mod.** Copy `db/**` to `db/import/`. When two mods ship the
  same table, **append the second one's Body**, as the app does. Replacing
  it silently drops the first. Copy `lua/` to `db/import/lua/`, and add one
  `npc:` line per script to `conf/import/map_conf.txt`. Print every `Done
  reading 'N' entries in 'db/import/...'` line and every Warning or Error.
- **Locking.** Serialise builds with a lock file. Two `make`s in one tree
  corrupt each other, and that happened in this work.
- **Client.** A small stdlib Python client at the same packet version: log
  in, create the character, enter the map, and run commands from stdin,
  printing JSON. It needs:
  - `say`, for @commands;
  - `whisper npc:<Name> a#b`, to drive a test NPC's `OnWhisperGlobal`;
  - `talk <npc>` (CZ_CONTACTNPC 0x90), with `menu N` answering `select()`;
  - `skill <id> <lv> <target>` (0x438) and `skill-pos`;
  - `skillup <id> [n]` (0x112);
  - `wear <idx> <pos>` (0x998);
  - `dump-damage <s>`, decoding ZC_NOTIFY_SKILL (0x1de), ZC_NOTIFY_ACT and
    skill_fail.

  Packet obfuscation keys are zero for every client after 2018-03-07, so no
  XOR is needed.
- **Test helper NPC** (test-only, never in the mod), driven by whisper:
  - `reset`, `ninja` (99/70), `strip` (`clearitem; Zeny = 0; SkillPoint = 0;`);
  - `joblvl#n`, `setjob#id`, `warp`;
  - `give#id` (prints the inventory indexes for `wear`), `eq#id`;
  - `build#job#weapon` (the §7 template), `dummy` (spawns the target beside
    you), `heal`;
  - `drops#mob` (`getmobdrops`);
  - `state` (class, levels, skill and status points, the path variable, the
    sums of learned skill levels per tree).

### Things that misled the tests

- `@itemreset` **skips equipped items**, so `Weight` stays above 0 and the
  rebirth NPC rightly refuses. Use `clearitem`.
- The script `equip` command always uses the item's own position, the right
  hand. Dual-wielding and the second accessory slot can only be tested with
  the client's wear packet (`0x22` both hands, `0x88` both accessories).
- A test character that never learned Basic Skill stays in the Novice tree
  (§4). That is correct, and not a bug in the mod.
- A self-buff such as Shadow Hiding, cast early in a skill sweep, blocks
  every skill after it. Cast it last.
- `@allskill` and GM groups with the all-skill permission bypass
  `skillup_limit`. Test the skill-point rules on a **group 0** account.
- Logging the same account in again too quickly gives "already online". Wait
  about 6 s between runs.
- A female account is needed for the female half of a split class.

### Checklist

- [ ] The map server loads the mod with 0 errors, and every table reports its
      entries.
- [ ] Path: each refusal (items still carried, low level, unspent points, the
      wrong class), rebirth (48 status points), base class again (100), the
      change (the right job id for each sex).
- [ ] Skill points: points saved before the change unlock only base-class
      skills; the expanded tree opens after the base share is spent;
      expanded-class points can buy base-class skills.
- [ ] Caps: max job, base 99.
- [ ] Gear: the base class's items and **ammo** can be worn; the new items
      can't be worn by the base class; dual-wielding; both accessories;
      headgear slots match the look; the set bonus applies when the last piece
      goes on.
- [ ] Every skill once: damage, or the status it should apply (status ids
      arrive in the status-change packet). Explain each failure (wrong
      weapon, missing ammo or charm, an order dependency) or fix it.
- [ ] Damage table as in §7.
- [ ] Drops: `getmobdrops` lists both new items for every monster in
      `drops.csv`.
- [ ] Shop: the base class is refused; the expanded class receives the item
      list (ZC_PC_PURCHASE_ITEMLIST).
- [ ] `System/itemInfo.lua` and the Lua hooks load in a Lua 5.4 interpreter.
      rAthena's `3rdparty/lua/src` has no `lua.c`, so compile a ten-line host
      around `luaL_dostring`.
- [ ] `build.py --check` passes.

---

## 9. Committing

- Work on a topic branch, never `main`. Stage only the mod and its tool
  folder. This checkout often carries unrelated line-ending changes.
- Regenerate `registry/index.json` in a **clean worktree** of the commit
  (`git worktree add --detach`, `python3 scripts/mod-index.py`, then
  `--check`), copy it back, and commit it separately. Run in the main
  checkout, it picks up line-ending changes to other mods' digests. Note
  that `scripts/mod-index.py --help` *writes* the index rather than printing
  help.
- `node --test tests/mod-registry.test.cjs`.
- Commit messages: a `mods:` tag, what the mod does, what it measured, and
  the co-author trailer.

---

## 10. Where the human has to come in

An agent can do everything above up to a committed, server-tested branch. It
cannot do the following, so stop and ask:

| When | What the human does |
|---|---|
| Before starting | The decisions in §1: path, power target and reference class, max job, gear scope and sources, names. |
| After the first measurements | Accept or adjust the balance table, and say whether gaps like Kunai Explosion's 0.70 are fine. |
| Drop rates and monsters | Sign off the list: it shapes where players spend weeks. |
| Before a PR | **Look at it in the real client**, which the headless rig cannot do: the class sprite for each sex, the item names, icons and descriptions, the weapon looks while attacking, the shop window, the skill tree window. |
| Before a PR | Check `requires.app` against the release that will carry it. |
| Pushing and PRs | This WSL host has no GitHub credentials. The human pushes and opens the PR. |
| Anything that needs a fork change | Don't make one. If a feature truly needs one, propose the smallest general hook on an issue first (see the app's `CLAUDE.md`). |

---

## 11. Third classes: Star Emperor, Soul Reaper

Renewal's Star Emperor and Soul Reaper are not expanded second classes like
Kagerou and Rebellion: rAthena makes them **third** classes (`JOBL_THIRD`) on
top of Star Gladiator and Soul Linker. That changes the recipe, mostly for
the better. The worked example is the Star Emperor (`npc/star_emperor.txt`,
`lua/star_emperor.lua` and the `star_emperor` config).

- **The path is a true rebirth.** Pre-renewal never gave Star Gladiators or
  Soul Linkers one, so the third class becomes their transcendent form:
  SG/SL 99/50 → reborn Novice → Taekwon (+52 status points) → SE/SR from
  Taekwon job 40, to job 70. That is `9 + 49 + 69 = 127` skill points at
  Taekwon 50, exactly a transcendent class, and the 69 buy SG/SL skills and
  SE/SR skills alike (the tree inherits the second class's).
- **Change through the second class, at once.** A direct Taekwon → Star
  Emperor `jobchange` records the Taekwon job level as `change_level_3rd`,
  and `pc_calc_skilltree_normalize_job` then holds every Star Emperor skill
  back until that many points sit in Star Gladiator skills. The NPC does
  `jobchange Job_Star_Gladiator; jobchange Job_Star_Emperor;`: the second
  change happens at Star Gladiator job 1, so nothing is held back. Verified
  both ways on the test server. Stock commands only; no variable hacking.
- **No item flags.** `pc_job_can_use_item` reads only the first class and
  the 2-1/2-2 branch, so a Star Emperor already counts as a Star Gladiator;
  and `pc_isItemClass` (`#ifndef RENEWAL`) lets third classes wear
  transcendent-only items. Give the mod's own gear the second class's job key
  plus `Classes: Third: true`, so the second class cannot wear it.
- **The Union form** (`Star_Emperor2`, from SG_FUSION with a Soul Linker's
  Star spirit) needs its own job_stats entry and tree, as in renewal; it is
  reached only through the skill, not `jobchange`.
- **Skills the test map cannot reach.** Several SE/SR skills work only on
  PvP/GvG maps (`map_flag_vs` in `skill_check_condition_castbegin`: Nova
  Explosion, Star Emperor Advent, Gravity Control, the Books, Soul Division,
  Soul Explosion). Leave them unscaled or measure them on a PvP map.
- **Stances, combos and procs.** Kicks need their stance (Universe Stance
  holds all three); Full Moon Kick needs New Moon Kick's status; Solar Burst
  follows Prominence Kick in a very short combo window; Falling Star adds two
  extra hit skills to normal attacks on Flash-Kicked targets. Measure these
  as rotations (the measuring script takes `id:lv:self` setup casts and an
  `attack` pseudo-skill), and scale the extra hits too: Falling Star's took
  plain attacks to 1.8 times Sonic Blow.
- **Shared generator.** `registry/tools/expanded_class/expanded_class.py` is
  the generator as a module, the same file on every class mod's branch; a
  class's `build.py` is a config. It trims job bonuses down to `BONUS_TOTAL`
  when renewal's exceed it, skips item flags when `ITEM_JOB` is unset, takes
  an `ASPD` override, and applies the fixed cast time rule (§7) when
  `FIXED_CAST_TO_DELAY` is set. All four class mods use it.

---

## 12. Third classes as sidegrades of the transcendent classes

Renewal's other third classes sit on top of second classes that
pre-renewal already finishes with a transcendent class. They do not
become a rebirth; they become **the other way to finish one**: after the
Valkyrie, a High Thief picks Assassin Cross *or* Guillotine Cross. All of
them go into one mod, `registry/mods/transcendent-third-classes` (branch
`mods/transcendent-third-classes`), which grows a class at a time. So far:

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
| Minstrel / Wanderer | Clown / Gypsy | `valkyrie 55 54` / `55 56` |
| Genetic | Creator | `valkyrie 55 50` |
| Mechanic | Whitesmith | `valkyrie 42 50` |
| Sorcerer | Professor | `valkyrie 55 47` |

### Decided with the human (do not re-ask)

- **Sidegrade, at parity.** Not "a bit below" as in §1: the transcendent
  class is the yardstick, and the third class trades its strengths, not
  its total.
- **Its own skills, never the transcendent ones.** The third class keeps
  its first and second class's skills and gets its own; it never learns
  the transcendent class's (no EDP for a Guillotine Cross). Sharing them
  would make it an upgrade.
- **The inherited skill trees stay whole for now** (see the next section):
  balancing the numbers comes first.
- **Area damage is capped** for fighting classes (see below); casters
  whose job it is are exempt.
- **Permanent choice.** No NPC to swap back.
- **A few weapons per class, no full set**, usable by both paths.
- **Every stock item the mod changes says so in its description**, where
  the old text no longer adds up.
- **Split by sex** where renewal splits (Minstrel/Wanderer), as two classes.
- **Fourth classes are out**: their trait stats (P.ATK, S.MATK, RES, ...)
  only work under `#ifdef RENEWAL` in `battle.cpp`/`status.cpp`.
- **The Job Master is left alone.** The app's `common-npcs` mod loads
  rAthena's `npc/custom/jobmaster.txt` with `.ThirdClass = true`, which
  offers any second class at 99/50 its third class at job 1, skipping the
  rebirth. A report of "the NPC made my Assassin Cross a Guillotine Cross"
  is that NPC. The human decided not to touch other mods from this one.

### A bigger skill set than the transcendent class

A third class keeps its second class's skills and adds its own, so it
**chooses from many more skills** than its transcendent class:

| | Picks from | Skill levels on offer |
|---|---|---|
| Assassin Cross | Assassin (12 skills) + Assassin Cross (5) | about 118 |
| Guillotine Cross | Assassin (12) + Guillotine Cross (19) | about 185 |

It does **not learn more**: both have the same skill points (9 Novice,
49 from the first class, 69 from job 70), and neither comes near learning
everything. Its own skills also need second-class skills first (Cross
Impact and Rolling Cutter need Sonic Blow 10, Weapon Blocking needs
Left-Hand Mastery 5, Cloaking Exceed needs Cloaking 3), so it pays a tax
of twenty points or so before it reaches them.

The wider choice is still a real advantage, in flexibility rather than
damage, and the damage measurements below do not capture it. Say so in
the README. Trimming each third class's inherited tree to what its own
skills require was looked at and set aside for now: a mechanical rule
("keep only prerequisites") would take Magnificat and Gloria from the
Arch Bishop, Bowling Bash and Two-Hand Quicken from the Rune Knight and
Devotion from the Royal Guard. If it comes back, it needs a hand-made
list per class, agreed with the human.

### Area damage: renewal's problem, and the counter

Renewal gave almost every third class an area attack it could spam, and
levelling became gathering a crowd and pressing one button; players
dislike it. In pre-renewal area damage belongs to a few classes. So:

- **A fighting third class deals at most about half its best
  single-target damage to each target of an area.** An area attack then
  pays from about three targets, and against one or two its single-target
  skills stay better. The ratio to watch is *area damage per target ÷ the
  same class's best single target*; renewal's numbers put the Rune Knight
  at 0.8 before the cap.
- **Casters whose job area damage is are exempt** (the Warlock, like the
  High Wizard, about 0.6). A support caster's area spells sit lower (the
  Arch Bishop at about half a High Wizard's).
- If a skill still trivialises play at half damage, the next tools are a
  longer after-cast delay or cooldown (`SKILL_OVERRIDES`), a higher SP
  cost and a smaller `SplashArea`. A hard cap on targets hit is not
  possible from a mod: rAthena has none per skill, and the Lua hooks do
  not see how many targets a skill hit.

Where it landed: Rolling Cutter 0.45, Fatal Menace 0.48, Ignition Break
0.47, Dragon Breath 0.50, Wind Cutter 0.55, Overbrand 0.48, Earth Drive
0.50, Cannon Spear 0.50.

### Agree the identity before measuring

Write down with the human what each of the two classes is *for* before
choosing any factor; "parity" alone does not say what to scale. Then set
the targets from it, and report where a result misses the identity.

| Transcendent | Third class | Targets |
|---|---|---|
| Assassin Cross: single-target burst | Guillotine Cross: area, debuffs, poisons, counters, mobility | one target 0.9x |
| Stalker: one copied skill kept for good, Full Strip | Shadow Chaser: two copy slots, curses, decoys, traps | its bow attack 1.0x Double Strafe |
| High Priest: guardian (Assumptio), SP-efficient | Arch Bishop: party buffs and heals, battle priest | healing 0.9x on one, 1.0x on a party; offence half a High Wizard's area |
| Lord Knight: the duellist (Spiral Pierce, Frenzy) | Rune Knight: dragon rider, runes | one target 0.9x |
| Paladin: holy striker, martyr | Royal Guard: shield wall, protection | one target 0.9x |
| High Wizard: storm-caller (Mystical Amplification, Soul Drain) | Warlock: elementalist, stored spells | one target 0.9x of amplified, area 1.0x of amplified |

Ask what the transcendent class gives up before deciding what the third
class must not have (Preserve, Assumptio, Soul Drain): the loss is often
the real balance problem, and usually it is SP.

### The class

- **Use the `_T` job** (`Job_Guillotine_Cross_T`, 4065). It carries
  `JOBL_UPPER`, so it gets the transcendent HP factor and transcendent-only
  gear like any reborn class.
- **Ship the non-`_T` tree under the `_T` name** (`TREE_FROM`): renewal's
  `_T` trees inherit the transcendent class and its skills. Check on the
  server that a transcendent skill stays at 0.
- **Copy the transcendent class's tables**: `HP_FROM`, `SP_FROM`,
  `EXP_FROM` = the transcendent class, scale 1.0, its 69 job levels
  (`MAX_JOB_LEVEL=70`). Renewal's third-class job bonuses come to +43;
  `EXTRA_BONUS` tops them up to `BONUS_TOTAL=45`.
- Job ids: Rune Knight T 4060, Warlock T 4061, Arch Bishop T 4063,
  Guillotine Cross T 4065, Royal Guard T 4073, Shadow Chaser T 4079. High
  Mage is 4003 and High Archer 4004 (an easy test mistake).

### The changer

- **Beside its transcendent class's changer, on the wall side.** The stock
  changers stand in two rows in the Valkyrie's hall (`npc/jobs/2-1a/`,
  `2-2a/` give the cells), with two walkable cells between each and the
  wall: x 42 for the west row, 55 for the east. Check a cell with
  `checkcell(map, x, y, cell_chkpass)`.
- Conditions: `ADVJOB` is the transcendent class, `Class` is the High
  first class, job 40 or more, and **no unspent skill points**.
- Ask twice, say "permanent", then `jobchange <transcendent>;
  jobchange <third>_T; set ADVJOB, 0;`. Going through the transcendent
  class is the §11 trick: the third-class change happens at its job 1, so
  `change_level_3rd` holds nothing back.
- Test the stock changer's route too: it must still make the
  transcendent class, without third-class skills.

### Other NPCs a class may need

Pre-renewal lacks renewal's service NPCs; the mod ships what the class
cannot work without, as plainly as it can:
- **Dragon Breeder** (Rune Knight): only `setdragon` gives a dragon, and
  needs Dragon Training. Beside the Knights' Peco Peco Breeder in
  Prontera. The Royal Guard's gryphon is the Crusader's Peco Peco riding:
  nothing needed.
- **Spellbook Seller** (Warlock): renewal's books, sold where renewal's
  Lea stands (`geffen_in 175 112`) at renewal's deposits, one copy each.

### Gear

- `Classes: Upper` with the second class's job key lets **both**
  transcendent paths wear it (pre-renewal's `pc_isItemClass` lets a
  `JOBL_THIRD` class wear Upper items); a non-reborn second class cannot.
- Each weapon: one bonus for both paths, the same again for the
  transcendent class (or its own skill), and the third class's own skill
  at about twice that, through `if (Class == Job_...)` in the script. The
  generated description lists all three.
- **Benchmarks that depend on gear**: give test gear realistic values.
  Pre-renewal Spiral Pierce scales with weapon weight (a Lance's, 2500),
  Rapid Smiting and Shield Press with shield weight (a Stone Buckler's,
  1500); staves give MATK through `bMatkRate` (+15% is standard).
- **Shields need a `View`** (`view=True` on the kind copies the look's);
  pre-renewal's mace subtype is `Mace`, not `1hMace`.
- **Raise base level before an equip test**; dual wielding is tested with
  `wear <idx> 2` then `wear <idx> 32`.
- Check every class mod's `drops.csv` for the same monsters; rAthena keeps
  only ten drops each, and a monster may drop items of one class only.

### Stock items the mod changes

When the mod changes how a stock item behaves, its description must say
so wherever the old text no longer adds up (a decision of the human).
`ITEM_DESCRIPTIONS` copies the translation's whole entry for the item and
adds lines before its type block; the client takes each item from the
first table that names it, and a mod's comes first. Done for the rune
stones whose reuse delays and durations changed.

### Skill entries

The generator imports renewal's entry for each of the class's skills and
resets every field pre-renewal sets and renewal leaves out. What came up:

- Reset values for `Knockback`, `SplashArea`, `HitCount`, `Type` (None),
  `TargetType` (Passive) and a dropped `Requires` (costs to 0).
  `DamageFlags`/`Flags` are cleared key by key.
- **`Hit` cannot be reset**: renewal's default, DMG_NORMAL, has no YAML
  name. Pre-renewal's stays; it only changes how the hit is shown.
- **CopyFlags: write both copy types false.** rAthena clears one with
  `option &= FLAG` instead of `&= ~FLAG` (fix: rathena branch
  `fix/skill-copyflags-false`).
- **An item cost cannot be removed**: `ItemCost` entries overwrite by
  position and always need their item. The generator fails unless the
  skill is listed in `ITEMCOST_KEPT` (Comet keeps 2 Red Gemstones).
- **Renewal can drop or rework a skill.** Skills only pre-renewal has
  (LG_OVERBRAND_BRANDISH) keep pre-renewal's entry. Skills only renewal
  has come in whole (`NEW_SKILLS_FROM_RENEWAL`), and so can a table
  pre-renewal has no rows in (`COPY_TABLES`, the spellbook_db) and
  renewal-only items (`NEW_FROM_RENEWAL`).
- **Check that the C++ still runs pre-renewal's version.** Pre-renewal's
  active Reading Spellbook has no code behind it; only renewal's passive
  one with its books works.
- `SKILL_OVERRIDES` replace a whole field, nested (`"Requires.SpCost"`) or
  per level; `SKILL_FLAGS_ADD` sets one flag on another class's skill;
  `ITEM_FIELDS` sets a stock item's field (a value, or `"renewal"`).

### Mechanics to check before calling a skill broken

- `Requires: Status:` (Counter Slash needs a Weapon Blocking parry),
  `Requires: State:` (Dragon Breath needs a dragon), `TargetType`
  (Cross Ripper Slasher on yourself does nothing), item costs (Feint
  Bomb, Adoramus, Comet), and preparation (Tetra Vortex needs four
  summoned spheres). Fail causes are the `USESKILL_FAIL_*` enum in
  `src/map/clif.hpp`.
- **Consumables: check the item too.** Pre-renewal's rune stones have no
  reuse delay; renewal's do. Renewal buffs measured in minutes can be
  absurd here (Giant Growth: x3.5 auto-attacks for 15 minutes became a
  30-second burst every 3 minutes), and so can a consumable nuke with a
  short delay (Storm Blast: one Wyrd rune every 10 seconds, not every
  second).
- **Items that cast through `itemskill`** (spellbooks) only open the skill:
  the client then sends the skill request, as for a scroll. `unitskilluseid`
  (rune stones) casts directly.
- **Damage under another id**: Chain Lightning hits as
  WL_CHAINLIGHTNING_ATK, Tetra Vortex as its four element skills, Duple
  Light as its melee/magic skills. Count those, and scale those in Lua.
- **Before calling a skill broken, read the target's HP** (`mobhp#0`).
  `dump-damage` prints only what arrives while it streams, so a hit that
  lands during a `wait` is never shown. Storm Blast was wrongly reported
  as dealing no damage this way, and a rune's description said so; it
  hits for about 4400 and needed a longer rune delay, not a note.
- **Party-only skills** (Banding, Hesperus Lit, Ray of Genesis without
  Inspiration) cannot be measured alone; they stay as in renewal.
- **Openers are not rotations** (Back Stab from behind turns the target).

### Measuring

- **The harness can lie.** A new skill request restarts a cast in
  progress; a test dummy that hits back interrupts cast-time skills; a
  knockback skill pushes a dummy that never walks back out of reach. Use
  the anchored dummy (`dummy#4`: `Ai: 06`, `KnockBackImmune`). For
  instant skills spam at a fixed pace (`... 0.1`); for cast-time skills
  cast one at a time (`... 1 paced`, the client's `cast` command resends
  only when nothing answered); measure both ways and keep the higher.
  Neither is always right: one-at-a-time caught half of Hell Inferno's
  casts, and a fixed pace can fall out of step with a caster's rhythm and
  lose a fifth. A spec run can list several paces (`"step": [1.0, 1.5]`)
  with `"method": "best"`; give every caster that.
- **Traps** are set off by a monster stepping on them, which a dummy never
  does: place one on a free cell beside it (`"how": "near"`; a trap cannot
  go next to a unit) and set it off with Detonator, in turn (`"seq"`,
  0.5 s). A trap's damage is mostly DEX and INT, outside a ratio hook;
  only its weapon part scales.
- **A summon kept between runs** (a warg) is dismissed by the next run's
  summon, since the skill toggles it: the helper's build clears it.
- **Some skills deal their damage through another skill id** (Severe
  Rainstorm's hits are WM_SEVERE_RAINSTORM_MELEE): when a factor changes
  nothing, scale the sub-skill.
- **Item job keys are rAthena's, not the class names**: Bards and Dancers
  share `BardDancer` (the server reads an unknown key as every job and
  says so in map.log). Instruments must be `Gender: Male` and whips
  `Female` (the generator's weapon kinds carry it).
- **Measure each build a class is played with**: a performer's
  Reverberation and Metallic Sound are magic (an INT build), Severe
  Rainstorm physical (DEX).
- **A crown that spends consumables** (the Creator's Acid Demonstration,
  a Fire Bottle and an Acid Bottle a throw, about 12,700 a second) is not
  what the sidegrade is aimed at: aim at the transcendent class's
  everyday damage (Acid Terror) and leave the crown its own.
- **Ground units hit under another id** (Crazy Weed as GN_CRAZYWEED_ATK):
  list it in the run's `"count"`. Generator: `UNIT_KEPT` for a skill that
  was a ground unit in pre-renewal and is a status in renewal (Hell's
  Plant); pre-renewal's `ActiveInstance` limit stays when renewal's entry
  sets none.
- **Check that everything a new skill consumes can be bought.** Pre-renewal
  sells none of renewal's: cannonballs, Magic Gear Fuel, Special Alloy
  Traps, Protect Neck Candy, the Genetic's craft books. Add renewal's
  shop where renewal has it (the Black Marketeer in Einbroch, Harive in
  Comodo), or one beside the class's guild. A mount or machine the class
  needs (Madogear) wants an NPC too.
- **The template lacks quest skills**: `@allskill` skips them, and a
  Whitesmith's Cart Boost (so Cart Termination) needs Cart Revolution and
  Change Cart; the helper teaches them. A skill the character lacks is
  dropped by the server without any reply: `skilllv#id` shows the level.
- **Cart skills grow with the cart's weight**: fill it (`"cartload":
  "989:79"`; a full 8000 is refused) before measuring Cart Termination or
  a Genetic's Cart Tornado.
- **A mount changes what is equipped**: getting into the Madogear took the
  cannonballs off; equip ammunition after mounting.
- **A skill that borrows another skill's damage** (Spell Fist turns every
  blow into the bolt it held) is scaled through that skill, but only when
  it should be: a hook can test the caster's job and status
  (`c.caster:has_status("SC_SPELLFIST")`) and leave everyone else's bolts
  alone.
- **A copied table may name what pre-renewal lacks**: renewal's
  elemental_db holds the fourth class's spirits, whose EM_ skills
  pre-renewal does not have; COPY_TABLES takes a pattern of rows to leave
  out.
- **The counter can lie too.** Fire Rain reports each hit twice, from its
  unit and from the caster (the rig now counts it once); Chain Lightning
  reports as WL_CHAINLIGHTNING_ATK. When a figure looks out of line, run
  it with `HPCHECK=1`: `hp_dps` is what the dummy really lost.
- **One dummy is one target.** Chain Lightning strikes at least four
  times and, with one target in reach, all four hit it: on the dummy it is
  a single-target spell, and it was set as one. Before treating a run on
  one dummy as an area figure, check whether the skill piles its hits onto
  a lone target.
- **The rig's heals hide what a skill spends.** Every heal refills HP and
  SP (and `sphererefill#n` spirit spheres), so a skill that spends all SP
  (Asura Strike, Gates of Hell) or many spheres repeats far more often
  than in play. Compare such bursts per hit, and steady rotations per
  full SP bar (`NOHEAL=1`); give a burst skill a cooldown when renewal
  gave it none.
- **Resources the class holds, not spends.** Kagerou and Oboro charms
  (Fire, Ice, Wind, Earth) last five minutes and add to every ninjutsu of
  their element: +20% a charm to Ice Spear's every hit, +100% a charm to
  Kamaitachi and Exploding Dragon, so ten charms double or triple them. Only
  Release Ninja Spell spends them, so in play they are always up. A
  magical build measured without them is measured wrong: fill them first
  (`"charge": "3016:1:10"`). A plain Ninja cannot make charms, so this is
  the rebirth class's alone.
- **Magic defence punishes many small hits.** In pre-renewal a target's
  soft MDEF (from its INT and VIT) comes off every hit. Ice Spear's twelve
  small hits keep about half their damage against a warded target (MDEF
  40, INT 80, VIT 50: `"dummy": "mdef"`); Jupitel Thunder, also twelve hits
  but bigger ones, about two thirds; Kamaitachi's single hit more. The
  more a skill is scaled down, the smaller each hit and the larger the
  share MDEF takes. Measure magic on both dummies and do not
  scale a multi-hit class down from the standard dummy alone, or it is
  useless against the monsters that matter.
- **Pair skills.** Cross Slash's Cross Wound is meant for a Kagerou and an
  Oboro alternating, but rAthena lets a caster's own wound count: the
  solo figure already includes the bonus. Measure such a skill both with
  and without it (one cast on a fresh target, then the rotation).
- **Renewal cadence can be absurd** (Cross Impact twice a second). When a
  skill's role is a big hit, lengthen its delay and then scale it, rather
  than scaling it into a pile of small hits.
- **Stack and payoff skills** (Rolling Cutter → Cross Ripper Slasher):
  measure the rotation at the fastest pace the server takes, and a
  relaxed one.
- **Amplifiers and procs**: measure the transcendent class with its own
  (Mystical Amplification, at its real max level), report debuffs like
  Dark Crow as burst windows, and measure auto-attacks with every proc
  buff on (Duple Light's magic strike beat casting until scaled).
- **SP is part of the balance.** Measure the net drain directly
  (`NOHEAL=1`: SP before and after, regeneration included) and compare
  **damage per full SP bar** with the transcendent class's best rotation.
  Renewal prices skills for renewal's SP pools; without its SP skills
  (Meditatio, Mana Recharge, Soul Drain) a third class ran dry two to
  three times faster. Lower its costs (`"Requires.SpCost"`) before
  touching damage. Soul Drain also returns SP for single-target kills;
  that free sustain stays the High Wizard's.
- Crit skills vary about 10% run to run; measure twice. Run one
  measurement at a time: two on the same map kill each other's dummies.

### Generator

`registry/tools/expanded_class/` holds the generator `expanded_class.py` and
the balance rig `balance/`. Every class is a config in the one `build.py`,
each with its CSVs in its own directory (`CSV_DIR`); after a generator
change, run `build.py --check` and read the diff. If the pinned
`vendor/rathena` lacks the pinned commit, pass `--rathena ../rathena`. When
two classes flag the same stock item for their jobs (the Awakening Potions
for Kagerou and Rebellion), the generator writes one entry with both keys:
rAthena takes an import entry's `Jobs:` as a whole, so two entries would
leave only the last class's. A monster may drop only one class's gear.

### Per new third class, in short

1. Agree the identities and targets with the human, including what the
   transcendent class's lost skills mean (often SP).
2. Add the class's config to the mod's `build.py`, and its weapons and
   drops to the CSVs; fix what the generator refuses.
3. Write its changer beside the transcendent changer, and any NPC the
   class cannot work without.
4. Test the path both ways, the transcendent skills blocked, the gear on
   both paths, the drops, and the class's own mechanics end to end.
5. Write the class's runs into the mod's `balance.json` (the
   transcendent class's rotations, the new class's, the aims), run it,
   set factors, overrides and SP costs, keep fighting classes' area damage
   at half their single target, and run it again until it exits 0.
6. Update the README (identity, numbers, changed stock items), `mod.json`
   and the Lua comments; reindex; sync the generator.

---

## Appendix: the mod's file list

```
registry/mods/transcendent-third-classes/
  mod.json, README.md        every class: the path, the numbers, the gear
  npc/<class>.txt            each class's changer (and its shops, breeders, sellers)
  lua/third_classes.lua      the third classes' ratio factors and measured table
  lua/<class>.lua            each expanded class's (kagerou_oboro, rebellion, ...)
  db/job_stats.yml           generated, every class
  db/skill_tree.yml          generated
  db/skill_db.yml            generated: renewal entries, resets, SKILL_OVERRIDES
  db/item_db.yml             generated: class flags on base-class items, the gear
  db/item_combos.yml         generated
  db/mob_db.yml              generated: the gear's drops
  db/spellbook_db.yml        generated (COPY_TABLES): the Warlock's
  System/itemInfo.lua        generated
registry/tools/transcendent-third-classes/
  build.py                   a config per class; [--rathena DIR] [--commit SHA] [--check]
  <class>/                   equipment.csv  drops.csv  combos.csv
  balance.json               the third classes' measuring runs
  balance-<class>.json       each expanded class's
```
