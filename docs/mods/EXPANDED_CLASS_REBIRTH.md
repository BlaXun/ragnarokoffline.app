# A renewal expanded class in pre-renewal, by rebirth

How to bring one of renewal's expanded second classes (Kagerou/Oboro,
Rebellion, ...) to a **pre-renewal** server as a mod, reached the way a
transcendent class is: by rebirth. It is written for an AI agent doing the
work, and says where the person it works for has to decide or check
something.

The worked example is [`registry/mods/kagerou-oboro`](../../registry/mods/kagerou-oboro),
with its generator in [`registry/tools/kagerou-oboro`](../../registry/tools/kagerou-oboro).
Read both before starting. Most of what follows is what that mod ran into.

---

## 0. The shape of the work

The result is **one registry mod, era `pre-renewal`**, that changes nothing in
rAthena, the population engine or the app. rAthena already compiles every
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

Everything under `db/` and `System/` is **generated** by a script in
`registry/tools/<mod>/`, from the pinned rAthena plus CSV files a person
edits. The NPC and the Lua are written by hand. The generator never ships with
the mod.

If you find yourself wanting to edit rAthena, stop and ask: the point of this
recipe is that it does not need to.

---

## 1. Decisions the human makes first

Ask these before writing anything. Each has a default from the Kagerou mod;
offer it, but let the person choose.

1. **The path.** Default: base class 99/70 → reborn as a plain Novice →
   Novice job 10 → base class again → expanded class from base-class job 50.
2. **Power target.** Kagerou's owner chose "a little below the transcendent
   classes". Ask whether it is on par, a bit below or below, and **which
   transcendent class to compare against** (melee: Assassin Cross; ranged:
   Sniper; caster: High Wizard).
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
  cannot reach. Kunai Splash got Sonic Blow's 2 s delay. Put such overrides
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
   final table in the Lua file's header and in the README.
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

Kagerou's final numbers (damage per second against an Assassin Cross):

| Kagerou | Assassin Cross | Ratio |
|---|---|---|
| Cross Slash + Soul Cutter: 875 | Sonic Blow: 1,020 | 0.86 |
| Swirling Petal: 975 | Meteor Assault: 1,180 | 0.83 |
| Kunai Splash: 813 | Meteor Assault: 1,180 | 0.69 |
| Kunai Explosion: 830 | Meteor Assault: 1,180 | 0.70 |

**The human decides whether those ratios are right.** Show them the table,
and say what it leaves out:
- buffs on both sides (Kagemusya, Enchant Deadly Poison);
- gear bonuses;
- auto-attacks between skills;
- PvP.

---

## 8. Testing without the app

`scripts/rotest` needs the app, and so macOS. On Linux or WSL, build a
headless rig instead. In the Kagerou work this was a scratchpad folder, which
does not survive the session, so rebuild it from this description:

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
the better. The worked example is `registry/mods/star-emperor` (branch
`mods/star-emperor`).

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

## 12. Third classes as sidegrades: Guillotine Cross

Renewal's other third classes (Guillotine Cross, Rune Knight, Arch Bishop,
...) sit on top of second classes that pre-renewal already finishes with a
transcendent class. They do not become a rebirth; they become **the other
way to finish one**: after the Valkyrie, a High Thief picks Assassin Cross
*or* Guillotine Cross. All of them go into one mod,
`registry/mods/transcendent-third-classes` (branch
`mods/transcendent-third-classes`), which grows a class at a time; the
Guillotine Cross was the pilot.

### Decided with the human (do not re-ask)

- **Sidegrade, at parity.** Not "a bit below" as in §1: the transcendent
  class is the yardstick, and the third class trades its strengths, not
  its total.
- **Its own skills only.** The third class keeps its first and second
  class's skills and gets its own, and never learns the transcendent ones
  (no EDP for a Guillotine Cross). Sharing the transcendent skills would
  make it an upgrade.
- **Permanent choice.** No NPC to swap back.
- **A few weapons, no full set**, and the transcendent class may use them
  too (see Gear).
- **Split by sex** where renewal splits (Minstrel/Wanderer), as two
  classes.
- **Fourth classes are out**: their trait stats (P.ATK, S.MATK, RES, ...)
  only work under `#ifdef RENEWAL` in `battle.cpp`/`status.cpp`.

### Agree the identity before measuring

Write down with the human what each of the two classes is *for* before
choosing any factor; "parity" alone does not say what to scale. For the
Assassin's pair:

- **Assassin Cross**: single-target burst (Sonic Blow, EDP windows). It
  keeps the single-target crown.
- **Guillotine Cross**: about 0.9 times that on one target, in return for
  a wider area (Rolling Cutter), a debuff (Dark Crow), poisons with
  effects, parry and counter (Weapon Blocking → Counter Slash) and
  mobility (Hallucination Walk, Cloaking Exceed, Dark Illusion).

Then set the targets from it: which rotation is compared with which, and
at what ratio. Report where the result misses the identity: the
Guillotine Cross's Rolling Cutter came out at 704 per target against
Meteor Assault's 1176, so it beats the Assassin Cross on groups only
through its larger area.

### The class

- **Use the `_T` job** (`Job_Guillotine_Cross_T`, 4065). It carries
  `JOBL_UPPER`, so it gets the transcendent HP factor and transcendent-only
  gear like any reborn class.
- **Ship the non-`_T` tree under the `_T` name.** Renewal's
  `Guillotine_Cross_T` tree inherits Assassin Cross and its skills; the
  plain `Guillotine_Cross` tree inherits only Assassin. The generator's
  `TREE_FROM={"Guillotine_Cross_T": "Guillotine_Cross"}` does this. Check
  on the server that a transcendent skill stays at 0 (`skillup 378` for
  EDP).
- **Copy the transcendent class's tables**: `HP_FROM`, `SP_FROM`,
  `EXP_FROM` = the transcendent class, scale 1.0, its 69 job levels
  (`MAX_JOB_LEVEL=70`). Renewal's third-class job bonuses fall short of
  45; top them up with `EXTRA_BONUS` to `BONUS_TOTAL=45`.

### The changer

- An NPC beside the Valkyrie (`valkyrie 52 58`), next to where the stock
  route goes on. The stock changer is left as it was; test that its route
  still makes the transcendent class without third-class skills.
- Conditions: `ADVJOB` is the transcendent class (so the player came
  through the Valkyrie for this branch), `Class` is the High first class,
  job 40 or more, and **no unspent skill points**, since they would be
  carried into a tree they were not earned for.
- Ask twice, say "permanent", then `jobchange <transcendent>;
  jobchange <third>_T; set ADVJOB, 0;`. Going through the transcendent
  class is the §11 trick: the third-class change happens at its job 1, so
  `change_level_3rd` holds nothing back.

### Gear

- `Classes: Upper` with the second class's job key lets **both**
  transcendent paths wear it: pre-renewal's `pc_isItemClass` lets a
  `JOBL_THIRD` class wear Upper items. A non-reborn second class cannot.
  `Classes: Third` would lock the transcendent class out; the human chose
  against that.
- Give each weapon bonuses for both paths (two skills of each), so
  neither class gets dead weight.
- Assassin-branch third classes dual-wield daggers through the upper
  mask, with no flag. Test it as the client does: `wear <idx> 2`, then
  `wear <idx> 32` (left hand).
- **Raise base level before an equip test.** A level-70 item on a level-1
  test character fails silently and looks like a class-flag bug.
- Check the other class mods' `drops.csv` for the same monsters; rAthena
  keeps only ten drops each.

### Skill entries

- Renewal entries can leave a `Knockback:` that pre-renewal sets and
  renewal does not; the generator now resets it to 0.
- `SKILL_OVERRIDES` replaces a whole field, a per-level list included.
  Before this it replaced only the first line and left the list behind.
- **Read `Requires: Status:` before calling a skill broken.** Counter Slash
  fails with cause 31 (`USESKILL_FAIL_GC_WEAPONBLOCKING`) until Weapon
  Blocking has parried a hit; Venom Pressure needs a poison on the blade;
  Cross Ripper Slasher needs Rolling Cutter's status. Fail causes are the
  `USESKILL_FAIL_*` enum in `src/map/clif.hpp`.
- **Read `TargetType`.** Cross Ripper Slasher cast on yourself does
  nothing and reports nothing; it needs the target.

### Measuring

- **Renewal cadence can be absurd here.** Cross Impact has 0.5 s delay and
  a 0.35 s cooldown at level 5, which renewal pays for with its stats; in
  pre-renewal that was nine times Sonic Blow. A factor alone would have
  made it a pile of small hits; overriding its delay to 1.5 s and then
  scaling (29%) kept it the heavy hit. Prefer that when a skill's role is
  a big hit.
- **Stack and payoff skills.** Cross Ripper Slasher gains 200% per Rolling
  Cutter counter, up to ten, and does not consume them, so the best
  rotation is to alternate the two. Measure at the fastest cadence the
  server accepts: here 0.35 s (`... mob - 0.35 seq`); at 0.3 s every Cross
  Ripper Slasher arrives inside Rolling Cutter's delay and is dropped
  without a failure packet. Report the perfect number and a relaxed one
  (0.5 s): 964 and 688.
- **Amplifying debuffs.** Dark Crow adds 30% per level to *short-range*
  damage on its target for 20 s a minute (half on bosses). Weapon skills
  with range 5 or more are long range and do not gain from it. Measure
  without it and describe it as the burst window.
- **Passives explain gaps.** The Guillotine Cross auto-attacks for 470
  against the Assassin Cross's 614: Advanced Katar Mastery is an Assassin
  Cross skill. That is the trade, not a bug.
- Crit skills (Cross Impact) vary by about 10% run to run; measure 60 s,
  twice.
- A skill that needs a consumable through a client menu (Venom Pressure)
  can be scaled from its ratio relative to a measured skill. Say so in the
  README.

### Generator

The four class mods' branches carry the same
`registry/tools/expanded_class/expanded_class.py`; this branch added
`TREE_FROM`, the Knockback reset and the whole-field override. Sync it to
every branch and confirm with `--check` that each mod's output does not
change. If the pinned `vendor/rathena` lacks the pinned commit, pass
`--rathena ../rathena`.

### Added with the Shadow Chaser

- **Several classes, one mod.** `run()` takes a list of configs, one per
  class, and joins their tables; each class keeps its CSVs in its own
  directory (`CSV_DIR`). A monster may drop items of one class only. A
  single config builds exactly as before.
- **The changers' places.** The stock transcendent changers stand in two
  rows in the Valkyrie's hall (`npc/jobs/2-1a/`, `2-2a/` give the cells),
  with two walkable cells between each and the wall. Each third class's
  changer stands right beside its transcendent class's, on the wall side
  (x 42 for the west row, 55 for the east): Guillotine Cross 42,58,
  Shadow Chaser 55,58, Arch Bishop 42,42. Check a cell with
  `checkcell(map, x, y, cell_chkpass)`.
- **The Job Master is a back door.** The app's `common-npcs` mod loads
  rAthena's `npc/custom/jobmaster.txt` with `.ThirdClass = true`: it
  offers any second class at 99/50 its third class at job 1, skipping
  the rebirth (and its expanded-class option skips Kagerou's and
  Rebellion's paths). A report of "the NPC made my Assassin Cross a
  Guillotine Cross" is this NPC, not the mod's. Not fixed yet.
- **Ask what the transcendent class gives up before deciding what the
  third class must not have.** Renewal's non-transcendent Shadow Chaser
  tree has no Preserve: Reproduce, a second slot written only during its
  five-minute window, is its kept copy. It copies first and second class
  skills (163 in all), not only third class ones.
- **Flags on other classes' skills.** `SKILL_FLAGS_ADD` writes an import
  entry with only that flag (Flags merge key by key). Check the C++ before
  adding one: Auto Shadow Spell skips Holy Light and Magnus Exorcismus by
  name, casts a self skill as a support skill on the enemy, and pays item
  costs it may not have.
- **Openers are not rotations.** In pre-renewal Back Stab works only from
  behind, and turns the target to face you; compare against what a class
  can repeat (the Stalker's Double Strafe).
- **Skills with item costs** (Feint Bomb: Paint Brush, Surface Paint) need
  the items on the test character, or they fail with nothing logged.
- **Testing copied skills**: a test monster with a `mob_skill_db.txt`
  entry casting the spell at you, Reproduce first, then Auto Shadow Spell's
  selection packet (`0x442`, answered with `0x443`). The list it sends
  shows which flags took effect.

### Added with the Arch Bishop

- **Measure SP, not just output, for a support class.** Renewal prices
  third-class skills for renewal's SP pools and SP gear; on a transcendent
  class's pool, without its SP skills (Meditatio, Mana Recharge), the Arch
  Bishop sustained half a High Priest's healing. Model a minute of party
  play: buff upkeep (durations and costs from the tables), heal per SP,
  SP recovered (`sp#0`, wait, read), with Magnificat for both. Balance
  heals by SP cost, buffs by "what five single buffs cost the other
  class".
- **`SKILL_OVERRIDES` reach nested fields** (`"Requires.SpCost"`) and take
  a list per level. A skill whose pre-renewal entry already matches
  renewal's is written anyway when it has an override.
- **Heals don't show as damage.** Drop HP to 1 (`hp#1`), cast, read HP;
  SP the same way. Subtract the SP regained between casts.
- **Passive procs can beat casting.** Duple Light's magic strike added
  645 dmg/s to staff auto-attacks on an INT build, more than Adoramus,
  for no SP. Measure auto-attacks with every proc buff on.
- **A support's damage benchmark is another class's.** The High Priest's
  own offence is weak, so the Arch Bishop's Holy magic was set against a
  High Wizard (0.7x), not against Holy Light.
- **`mod.json` takes at most 8 tags**; a growing mod should not tag each
  class.
- Pre-renewal's mace subtype is `Mace`, renewal's `1hMace`.

### Per new third class, in short

1. Agree identity and targets with the human.
2. Add the class to `JOBS`, `TREE_FROM`, the table sources, `EXTRA_BONUS`,
   `SKILL_PREFIX` and `EQUIP_JOBS` in the mod's `build.py`, and its
   weapons and drops to the CSVs.
3. Write its changer beside the Valkyrie.
4. Test the path both ways, the transcendent skills blocked, the gear on
   both paths, and the drops.
5. Measure against the transcendent class, set factors and overrides,
   remeasure, and add a section to the README and a line to `mod.json`.

---

## Appendix: Kagerou's file list

```
registry/mods/kagerou-oboro/
  mod.json                 era pre-renewal
  README.md                the path, the numbers, the gear, the files
  npc/kagerou_oboro.txt    Kirikage (rebirth and job change), Shadow Supplier, hidden shop
  lua/kagerou_oboro.lua    ratio factors and the measured table
  db/job_stats.yml         generated
  db/skill_tree.yml        generated
  db/skill_db.yml          generated: renewal entries, resets, SKILL_OVERRIDES
  db/item_db.yml           generated: class flags on Ninja items and ammo, 28 items
  db/item_combos.yml       generated
  db/mob_db.yml            generated
  System/itemInfo.lua      generated
registry/tools/kagerou-oboro/
  build.py                 [--rathena DIR] [--commit SHA] [--check]
  equipment.csv  drops.csv  combos.csv
```
