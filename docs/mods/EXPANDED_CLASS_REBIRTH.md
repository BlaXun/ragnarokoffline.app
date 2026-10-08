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

### Method

1. Build both characters from one template: base 99, max job, the same stats
   allocation, `@allskill`, and a test weapon of the same ATK for each class's
   weapon type (a 150-ATK Katar, Dagger, Huuma, ... defined in a *test-only*
   mod).
2. Use one immobile target: a test-only monster with a lot of HP, set DEF
   and VIT (Kagerou used 30/30), `NoRandomWalk`, and a negligible attack.
3. Spam the skill every 0.1 s for 30 s, and total the damage the client
   receives. The server enforces delays and cooldowns itself, so spamming
   gives the real maximum rate.
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
