"""Shared generator for mods that bring a renewal expanded class to pre-renewal.

Each mod keeps a short build.py beside its CSV files that describes the class
(a config: jobs, base class, tables to scale, skill prefixes...) and calls
run(). docs/mods/EXPANDED_CLASS_REBIRTH.md is the guide; this module is the
part of it that is code. Standard library only.

What it writes, under registry/mods/<mod>/:
  db/job_stats.yml    the class's HP/SP, EXP tables, job bonuses, ASPD, weight
  db/skill_tree.yml   renewal's trees for the class, unchanged
  db/skill_db.yml     renewal's entries for the class's skills where
                      pre-renewal's differ, with every leftover field and
                      nested flag cleared
  db/item_db.yml      the class's job flag on the base class's items (when it
                      has its own flag), renewal-only items the skills need,
                      and the mod's equipment
  db/item_combos.yml  set bonuses;  db/mob_db.yml  drops
  System/itemInfo.lua the equipment's names, descriptions and art
"""

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path


from types import SimpleNamespace

C = None   # the running mod's config, set by run()

# Armour kinds every class shares; a config adds its weapon kinds.
ARMOR_KINDS = {
    "head":      dict(type="Armor",  sub=None,     loc=None,               label="Headgear",       unid="Hat"),
    "armor":     dict(type="Armor",  sub=None,     loc=["Armor"],          label="Armor",          unid="Armor"),
    "garment":   dict(type="Armor",  sub=None,     loc=["Garment"],        label="Garment",        unid="Garment"),
    "shoes":     dict(type="Armor",  sub=None,     loc=["Shoes"],          label="Shoes",          unid="Shoes"),
    "accessory": dict(type="Armor",  sub=None,     loc=["Both_Accessory"], label="Accessory",      unid="Accessory"),
}


def config(build_file, **kw):
    """A mod's settings. Required: MOD_NAME, JOBS, BASE, SKILL_PREFIX, HP_FROM,
    HP_SCALE, SP_FROM, SP_SCALE, EXP_FROM, BONUS_TOTAL, MAX_JOB_LEVEL,
    WEAPON_KINDS. See registry/tools/*/build.py for worked examples."""
    tool = Path(build_file).resolve().parent
    root = tool.parents[2]
    c = SimpleNamespace(
        ROOT=root, TOOL=tool,
        ITEMINFO=root / "vendor" / "ROenglishRE" / "Translation" / "Renewal" / "SystemEN" / "LuaFiles514" / "itemInfo.lua",
        ITEM_JOB=None,          # the class's own item_db Jobs: key, when it has one
        EQUIP_JOBS=None,        # Jobs: of the mod's equipment (default: [ITEM_JOB])
        EQUIP_CLASSES=None,     # Classes: of the mod's equipment, e.g. ["Third"]
        NEW_FROM_RENEWAL=[], SKILL_OVERRIDES={}, EXTRA_BONUS=[], WEAPON_KINDS={},
        # Pre-renewal has no fixed cast time: every cast time shrinks with
        # DEX, to nothing at 150. When set, this share of each skill's
        # renewal FixedCastTime becomes after-cast delay (which DEX does not
        # touch) and the rest is added to its CastTime. None leaves it.
        FIXED_CAST_TO_DELAY=None,
        # A skill whose cooldown is at least this long (ms) cannot be spammed
        # anyway: its whole fixed cast goes into CastTime, where DEX and
        # Izayoi reduce it as renewal's fixed-cast reductions would.
        FIXED_CAST_COOLDOWN_EXEMPT=10000,
        ASPD=None,              # {weapon: value} instead of the base class's BaseASPD
        # {job: renewal job}: ship that renewal job's tree under this job's
        # name (a transcendent third class with the non-transcendent tree).
        TREE_FROM={},
        # A subdirectory of the tool's directory holding this class's
        # equipment.csv, drops.csv and combos.csv, when one mod builds several
        # classes (run() given a list of configs). None: the tool's own.
        CSV_DIR=None,
        # The Requirement line of the equipment's descriptions; default: JOBS.
        EQUIP_LABEL=None,
        # The item table's note on the equipment; default: four tiers.
        ITEMS_ABOUT=None,
        # {flag: [skill names]}: Flags: this mod turns on for skills of other
        # classes (an import entry's Flags merge key by key, so only this one
        # is added), e.g. {"IsAutoShadowSpell": ["PR_TURNUNDEAD"]}.
        SKILL_FLAGS_ADD={},
        # {item aegis: {field: value}}: fields this mod sets on a stock item.
        # A value is "renewal" (copy the field, with everything under it,
        # from renewal's entry for the item) or a scalar or a dict of scalars.
        ITEM_FIELDS={})
    c.__dict__.update(kw)
    c.MOD = root / "registry" / "mods" / c.MOD_NAME
    c.KINDS = {**c.WEAPON_KINDS, **ARMOR_KINDS}
    c.CSV = tool / c.CSV_DIR if c.CSV_DIR else tool
    if c.EQUIP_JOBS is None:
        c.EQUIP_JOBS = [c.ITEM_JOB]
    return c


HEAD_POSITION = {"Head_Top": "Upper", "Head_Mid": "Middle", "Head_Low": "Lower"}

RULE = "_______________________"


def fail(msg):
    sys.exit(f"build.py ({C.MOD_NAME}): {msg}")


# ---------------------------------------------------------------- reading

def pinned_commit():
    for line in (C.ROOT / "config" / "VENDOR_PINS").read_text().splitlines():
        parts = line.split()
        if parts and parts[0] == "rathena":
            return parts[2]
    fail("no rathena line in config/VENDOR_PINS")


def git_show(repo, commit, path):
    try:
        out = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"],
                             check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        fail(f"git show {commit}:{path} in {repo}: {e.stderr.decode().strip()}\n"
             f"  (fetch the pin, or pass --rathena with a checkout that has it)")
    return out.stdout.decode("utf-8").replace("\r\n", "\n")


def body_entries(text, key):
    """Split a YAML table's Body into entries, each starting with `  - <key>:`."""
    if "\nBody:\n" not in text:
        fail("table without a Body")
    body = text.split("\nBody:\n", 1)[1].split("\nFooter:", 1)[0]
    parts = re.split(r"\n(?=  - " + key + r":)", "\n" + body)
    return [p.strip("\n") for p in parts if p.strip().startswith(f"- {key}:")]


def entry_jobs(entry):
    m = re.search(r"^(?:  - |    )Jobs:\n((?:      \w+: \w+\n?)+)", entry + "\n", re.M)
    return dict(re.findall(r"^      (\w+): (\w+)", m.group(1), re.M)) if m else {}


def section(entry, name):
    """The lines of a top-level key's block, its header line excluded."""
    m = re.search(r"^(?:  - |    )" + name + r":\n((?:      .*\n?)+)", entry + "\n", re.M)
    return m.group(1).rstrip("\n").split("\n") if m else None


def job_block(entries, job, key):
    for e in entries:
        if entry_jobs(e).get(job) == "true" and section(e, key) is not None:
            return e
    fail(f"no {key} for {job}")


def level_values(lines, field):
    pairs = re.findall(r"- Level: (\d+)\n\s+" + field + r": (\d+)", "\n".join(lines))
    if not pairs:
        fail(f"no {field} levels")
    return [(int(l), int(v)) for l, v in pairs]


def by_field(entries, field):
    out = {}
    for e in entries:
        m = re.search(r"^    " + field + r": (.+)$", e, re.M)
        if m:
            out[m.group(1).strip()] = e
    return out


def lua_items(path):
    """The translation's item table, by id. It is cp949 with a few stray bytes."""
    text = path.read_bytes().decode("cp949", errors="replace").replace("\r\n", "\n")
    items = {}
    for m in re.finditer(r"\n\t\[(\d+)\] = \{\n(.*?)\n\t\},", text, re.S):
        body = m.group(2)
        f = lambda k: (re.search(r"\n?\t\t" + k + r' = "([^"]*)"', body) or [None, None])[1]
        cls = re.search(r"\t\tClassNum = (\d+)", body)
        items[int(m.group(1))] = dict(
            unres=f("unidentifiedResourceName"), res=f("identifiedResourceName"),
            classnum=int(cls.group(1)) if cls else 0)
    if not items:
        fail(f"read no items from {path}")
    return items


# ---------------------------------------------------------------- writing

def header(kind, version, source, about):
    lines = [f"# Generated by registry/tools/{C.MOD_NAME}/build.py -- do not",
             "# hand-edit. Rerun it when config/VENDOR_PINS moves rAthena or a",
             "# CSV beside it changes.",
             f"# Source: {source}", "#"]
    lines += ["# " + l if l else "#" for l in about]
    lines += ["Header:", f"  Type: {kind}", f"  Version: {version}", "", "Body:"]
    return "\n".join(lines) + "\n"


def yaml_str(s):
    return s if re.fullmatch(r"[A-Za-z0-9_' .()-]+", s) and not s[0] in "'-" else '"' + s.replace('"', '\\"') + '"'


def build_job_stats(src):
    stats = body_entries(src["db/pre-re/job_stats.yml"], "Jobs")
    exp = body_entries(src["db/pre-re/job_exp.yml"], "Jobs")
    points = body_entries(src["db/pre-re/job_basepoints.yml"], "Jobs")
    re_stats = body_entries(src["db/re/job_stats.yml"], "Jobs")

    renewal = job_block(re_stats, C.JOBS[0], "BonusStats")
    bonus = re.findall(r"- Level: (\d+)\n((?:\s{8}\w+: -?\d+\n?)+)", "\n".join(section(renewal, "BonusStats")) + "\n")
    bonus = [(int(l), st, int(v)) for l, body in bonus for st, v in re.findall(r"(\w+): (-?\d+)", body)
             if int(l) <= C.MAX_JOB_LEVEL]
    bonus += [(l, st, 1) for l, st in C.EXTRA_BONUS]
    # More than the target: drop renewal's highest-level bonuses first.
    bonus.sort()
    dropped_bonus = []
    while sum(v for _, _, v in bonus) > C.BONUS_TOTAL and bonus:
        dropped_bonus.append(bonus.pop())
    if sum(v for _, _, v in bonus) != C.BONUS_TOTAL:
        fail(f"job bonuses add up to {sum(v for _, _, v in bonus)}, not {C.BONUS_TOTAL}: adjust EXTRA_BONUS")

    base_exp = job_block(exp, C.EXP_FROM, "BaseExp")
    max_base = re.search(r"^    MaxBaseLevel: (\d+)", base_exp, re.M).group(1)
    job_exp = job_block(exp, C.EXP_FROM, "JobExp")
    job_levels = [(l, v) for l, v in level_values(section(job_exp, "JobExp"), "Exp") if l < C.MAX_JOB_LEVEL]
    if len(job_levels) != C.MAX_JOB_LEVEL - 1:
        fail("the transcendent job EXP table is shorter than expected")

    hp = level_values(section(job_block(points, C.HP_FROM, "BaseHp"), "BaseHp"), "Hp")
    sp = level_values(section(job_block(points, C.SP_FROM, "BaseSp"), "BaseSp"), "Sp")
    base_stats = job_block(stats, C.BASE, "BonusStats")
    weight = re.search(r"^    MaxWeight: (\d+)", base_stats, re.M).group(1)
    hp_factor = re.search(r"^    HpFactor: (\d+)", base_stats, re.M).group(1)
    sp_increase = (re.search(r"^    SpIncrease: (\d+)", base_stats, re.M) or [None, "100"])[1]
    aspd = section(job_block(body_entries(src["db/pre-re/job_aspd.yml"], "Jobs"), C.BASE, "BaseASPD"), "BaseASPD")

    jobs = ["  - Jobs:"] + [f"      {j}: true" for j in C.JOBS]
    out = list(jobs)
    out += [f"    MaxWeight: {weight}", f"    HpFactor: {hp_factor}", f"    SpIncrease: {sp_increase}", "    BaseASPD:"]
    out += [f"      {k}: {v}" for k, v in C.ASPD.items()] if C.ASPD else aspd
    out += ["    BonusStats:"]
    by_level = {}
    for lvl, stat, val in bonus:
        by_level.setdefault(lvl, {}).setdefault(stat, 0)
        by_level[lvl][stat] += val
    for lvl in sorted(by_level):
        out.append(f"      - Level: {lvl}")
        out += [f"        {stat}: {val}" for stat, val in by_level[lvl].items()]
    out += [f"    MaxBaseLevel: {max_base}", "    BaseExp:"]
    for lvl, val in level_values(section(base_exp, "BaseExp"), "Exp"):
        out += [f"      - Level: {lvl}", f"        Exp: {val}"]
    out += [f"    MaxJobLevel: {C.MAX_JOB_LEVEL}", "    JobExp:"]
    for lvl, val in job_levels:
        out += [f"      - Level: {lvl}", f"        Exp: {val}"]
    out += ["    BaseHp:"]
    for lvl, val in hp:
        out += [f"      - Level: {lvl}", f"        Hp: {round(val * C.HP_SCALE)}"]
    out += ["    BaseSp:"]
    for lvl, val in sp:
        out += [f"      - Level: {lvl}", f"        Sp: {round(val * C.SP_SCALE)}"]

    totals = {}
    for _, s, v in bonus:
        totals[s] = totals.get(s, 0) + v
    about = [
        f"{', '.join(C.JOBS)}, which pre-renewal's job tables do not have.",
        f"Base levels 1-{max_base} on the transcendent EXP table, job levels",
        f"1-{C.MAX_JOB_LEVEL} on the transcendent second-job table (cut at {C.MAX_JOB_LEVEL}).",
        f"HP: {C.HP_FROM} x {C.HP_SCALE}. SP: {C.SP_FROM} x {C.SP_SCALE}. "
        + (f"Weight: the {C.BASE}'s. ASPD: " + ", ".join(f"{k} {v}" for k, v in C.ASPD.items()) + "."
           if C.ASPD else f"ASPD and weight: the {C.BASE}'s."),
        f"Job bonuses: renewal's to job {C.MAX_JOB_LEVEL}"
        + (", then one each at " + ", ".join(str(l) for l, _ in C.EXTRA_BONUS) if C.EXTRA_BONUS else "")
        + (f" less its last {len(dropped_bonus)}" if dropped_bonus else "")
        + f" (+{sum(totals.values())} in all).",
    ]
    return about, "\n".join(out) + "\n"


def build_skill_tree(src):
    tree = body_entries(src["db/re/skill_tree.yml"], "Job")
    by_job = {e.split("\n")[0].strip()[len("- Job: "):]: e for e in tree}
    out = []
    for job in C.JOBS:
        source = C.TREE_FROM.get(job, job)
        if source not in by_job:
            fail(f"renewal's skill tree has no {source}")
        entry = by_job[source]
        if source != job:
            entry = entry.replace(f"- Job: {source}", f"- Job: {job}    # renewal's {source} tree", 1)
        out.append(entry)
    about = [f"Renewal's {', '.join(C.JOBS)} tree, unchanged. It inherits Novice and",
             f"{C.BASE}, so every point earned after the change can also go into {C.BASE} skills."]
    if C.TREE_FROM:
        about = ["Renewal's trees for " + ", ".join(C.JOBS) + ", taken from "
                 + ", ".join(f"{s} for {j}" for j, s in C.TREE_FROM.items()) + ":",
                 "the class gets that job's skills and what it inherits, nothing more."]
    return about, "\n".join(out) + "\n"


SKILL_DEFAULTS = {"Element": "Neutral", "Range": "0", "Knockback": "0", "SplashArea": "0", "HitCount": "0", "AfterCastActDelay": "0", "AfterCastWalkDelay": "0", "Duration1": "0",
                  "Duration2": "0", "CastTime": "0", "Cooldown": "0", "FixedCastTime": "0"}


# Maps that an import entry merges key by key: a key the entry leaves out keeps
# pre-renewal's value. RL_D_TAIL kept pre-renewal's NoDamage this way, which
# made rAthena cast it as a no-damage skill: it spent its missile and hit
# nothing. Each leftover key is cleared explicitly.
FLAG_MAPS = ("DamageFlags", "Flags")
REQUIRE_MAPS = {"Ammo": "None", "Weapon": "All"}   # the key that clears the whole map
REQUIRE_UNCLEARABLE = ("Equipment", "State", "Status")


def true_keys(block, indent):
    return {k for k, v in re.findall(r"^" + " " * indent + r"(\w+): (\w+)", block, re.M) if v == "true"}


def map_block(text, key, indent):
    return re.search(r"^" + " " * indent + key + r":[^\n]*\n((?:" + " " * (indent + 2) + r".*\n?)*)", text, re.M)


def nested_resets(name, pre_e, entry):
    entry += "\n"
    for key in FLAG_MAPS:
        pm, rm = map_block(pre_e + "\n", key, 4), map_block(entry, key, 4)
        left = (true_keys(pm.group(1), 6) - (true_keys(rm.group(1), 6) if rm else set())) if pm else set()
        if not left:
            continue
        add = "".join(f"      {k}: false    # set in pre-renewal's entry; renewal's leaves it out\n" for k in sorted(left))
        entry = entry[:rm.end(1)] + add + entry[rm.end(1):] if rm else entry + f"    {key}:\n" + add
    preq = map_block(pre_e + "\n", "Requires", 4)
    if preq:
        for key in REQUIRE_UNCLEARABLE:
            pm = map_block(preq.group(1), key, 6)
            rreq = map_block(entry, "Requires", 4)
            rm = map_block(rreq.group(1), key, 6) if rreq else None
            if pm and true_keys(pm.group(1), 8) - (true_keys(rm.group(1), 8) if rm else set()):
                fail(f"{name}: pre-renewal's Requires.{key} has entries renewal's lacks, and there is no way to clear them")
        for key, clear in REQUIRE_MAPS.items():
            pm = map_block(preq.group(1), key, 6)
            if not pm:
                continue
            rreq = map_block(entry, "Requires", 4)
            rm = map_block(rreq.group(1), key, 6) if rreq else None
            left = true_keys(pm.group(1), 8) - (true_keys(rm.group(1), 8) if rm else set())
            if not left:
                continue
            if rm:
                add = "".join(f"        {k}: false    # required by pre-renewal's entry, not renewal's\n" for k in sorted(left))
                pos = rreq.start(1) + rm.end(1)
            else:
                add = (f"      {key}:    # pre-renewal's entry requires {', '.join(sorted(left))}; renewal's does not\n"
                       f"        {clear}: true\n")
                pos = rreq.end(1) if rreq else None
            if pos is None:
                entry += "    Requires:\n" + add
            else:
                entry = entry[:pos] + add + entry[pos:]
    return entry.rstrip("\n")


def level_values_of(entry, key, field, maxlv):
    """A per-level key as a list of maxlv ints: a scalar, a level list, or 0."""
    m = re.search(r"^    " + key + r": (\d+)", entry, re.M)
    if m:
        return [int(m.group(1))] * maxlv
    blk = re.search(r"^    " + key + r":[^\n]*\n((?:      .*\n?)*)", entry + "\n", re.M)
    if not blk:
        return [0] * maxlv
    vals = {int(l): int(v) for l, v in re.findall(r"- Level: (\d+)\n\s+" + field + r": (\d+)", blk.group(1))}
    out, last = [], 0
    for lv in range(1, maxlv + 1):          # rAthena repeats the last level given
        last = vals.get(lv, last)
        out.append(last)
    return out


def set_level_values(entry, key, field, values, note):
    """Replace (or add) a per-level key, as a scalar when every level agrees."""
    block = re.compile(r"^    " + key + r":[^\n]*\n(?:      .*\n)*|^    " + key + r": .*\n", re.M)
    if len(set(values)) == 1:
        text = f"    {key}: {values[0]}    # {note}\n"
    else:
        text = f"    {key}:    # {note}\n" + "".join(
            f"      - Level: {i}\n        {field}: {v}\n" for i, v in enumerate(values, 1))
    entry += "\n"
    if block.search(entry):
        entry = block.sub(lambda m: text, entry, count=1)
    else:
        entry += text
    return entry.rstrip("\n")


def fold_fixed_cast(name, entry):
    """Pre-renewal ignores FixedCastTime; turn it into delay and cast time."""
    share = C.FIXED_CAST_TO_DELAY
    maxlv = int(re.search(r"^    MaxLevel: (\d+)", entry, re.M).group(1))
    fixed = level_values_of(entry, "FixedCastTime", "Time", maxlv)
    if not any(fixed):
        return entry
    cast = level_values_of(entry, "CastTime", "Time", maxlv)
    delay = level_values_of(entry, "AfterCastActDelay", "Time", maxlv)
    cooldown = level_values_of(entry, "Cooldown", "Time", maxlv)
    exempt = C.FIXED_CAST_COOLDOWN_EXEMPT
    # Per level: a level whose cooldown is long enough keeps its whole fixed
    # cast as cast time; the others split it.
    long_cd = [exempt is not None and cd >= exempt for cd in cooldown]
    to_delay = [0 if lc else round(f * share) for f, lc in zip(fixed, long_cd)]
    if all(long_cd):
        note = f"renewal's FixedCastTime added here: a {min(cooldown) // 1000}s+ cooldown already stops spam"
    elif any(long_cd):
        note = (f"renewal's FixedCastTime: {int(share * 100)}% added to delay, the rest here;"
                f" levels with a {exempt // 1000}s+ cooldown keep all of it here")
    else:
        note = f"renewal's FixedCastTime: {int(share * 100)}% added here as delay, the rest to CastTime"
    if any(to_delay):
        entry = set_level_values(entry, "AfterCastActDelay", "Time", [d + t for d, t in zip(delay, to_delay)], note)
    entry = set_level_values(entry, "CastTime", "Time", [c + f - t for c, f, t in zip(cast, fixed, to_delay)], note)
    entry = set_level_values(entry, "FixedCastTime", "Time", [0] * maxlv, "moved into CastTime and AfterCastActDelay")
    return entry


# The per-level field name of each key that takes a level list.
LEVEL_FIELD = {"SpCost": "Amount", "HpCost": "Amount"}


def override_field(name, entry, key, value):
    """Replace a field, a per-level list under it included. KEY may name a
    field inside a map ("Requires.SpCost"); VALUE is a scalar or, for a
    per-level value, a list with one entry per level."""
    note = "this mod's balance; renewal's is different"
    *parents, field = key.split(".")
    indent = 4 + 2 * len(parents)
    pad = " " * indent
    if isinstance(value, list):
        sub = LEVEL_FIELD.get(field, "Time")
        text = f"{pad}{field}:    # {note}\n" + "".join(
            f"{pad}  - Level: {i}\n{pad}    {sub}: {x}\n" for i, x in enumerate(value, 1))
    else:
        text = f"{pad}{field}: {value}    # {note}\n"
    start, end = 0, len(entry) + 1
    body = entry + "\n"
    for i, p in enumerate(parents):          # narrow to the parent map's block
        m = re.compile(r"^" + " " * (4 + 2 * i) + p + r":[^\n]*\n((?:" + " " * (6 + 2 * i) + r".*\n)*)", re.M).search(body, start, end)
        if not m:
            fail(f"{name}: no {'.'.join(parents[:i + 1])} to override")
        start, end = m.start(1), m.end(1)
    m = re.compile(r"^" + pad + field + r":.*\n(?:" + pad + r"  .*\n)*", re.M).search(body, start, end)
    if not m:
        fail(f"{name}: no {key} to override")
    return (body[:m.start()] + text + body[m.end():]).rstrip("\n")


def build_skill_db(src):
    pre = by_field(body_entries(src["db/pre-re/skill_db.yml"], "Id"), "Name")
    ren = by_field(body_entries(src["db/re/skill_db.yml"], "Id"), "Name")
    names = sorted(n for n in pre if n.startswith(C.SKILL_PREFIX))
    out, changed, pre_only = [], [], []
    for n in names:
        if n not in ren:
            pre_only.append(n)          # an older revision's skill renewal dropped
            continue
        if pre[n] == ren[n] and n not in C.SKILL_OVERRIDES:
            continue
        keys = lambda e: set(re.findall(r"^    (\w+):", e, re.M))
        dropped = keys(pre[n]) - keys(ren[n])
        entry = ren[n]
        for k in sorted(dropped):
            if k == "CopyFlags":
                # Both keys false: rAthena's parser clears a copy flag with
                # `option &= FLAG` (not ~FLAG), so one false key alone keeps
                # the other's bit; both together clear it, fixed or not.
                entry += ("\n    CopyFlags:    # pre-renewal's entry lets Plagiarism/Reproduce copy it; renewal's does not"
                          "\n      Skill:\n        Plagiarism: false\n        Reproduce: false")
                continue
            if k in FLAG_MAPS:
                continue                # nested_resets clears it key by key
            if k == "Hit":
                # Renewal's default is DMG_NORMAL, which has no YAML name; Hit
                # only changes how the hit is shown, so pre-renewal's stays.
                entry += "\n    # Hit: pre-renewal's value stays (renewal's default, Normal, cannot be written)"
                continue
            if k not in SKILL_DEFAULTS:
                fail(f"{n}: pre-renewal sets {k}, renewal does not, and there is no reset value for it")
            entry += f"\n    {k}: {SKILL_DEFAULTS[k]}    # pre-renewal's entry sets this; renewal's does not"
        entry = nested_resets(n, pre[n], entry)
        if C.FIXED_CAST_TO_DELAY is not None:
            entry = fold_fixed_cast(n, entry)
        for k, v in C.SKILL_OVERRIDES.get(n, {}).items():
            entry = override_field(n, entry, k, v)
        out.append(entry)
        changed.append(n)
    added = []
    for flag, skills in C.SKILL_FLAGS_ADD.items():
        for n in skills:
            if n not in pre:
                fail(f"SKILL_FLAGS_ADD: {n} is not in pre-renewal's skill_db")
            if re.search(r"^      " + flag + r": true", pre[n], re.M):
                fail(f"SKILL_FLAGS_ADD: {n} already has {flag}")
            sid = re.match(r"- Id: (\d+)", pre[n].strip()).group(1)
            out.append(f"  - Id: {sid}\n    Name: {n}\n    Flags:\n      {flag}: true    # this mod's; pre-renewal's entry is otherwise kept")
            added.append(f"{flag} on {n}")
    prefixes = "/".join(C.SKILL_PREFIX) if isinstance(C.SKILL_PREFIX, tuple) else C.SKILL_PREFIX
    about = [f"Renewal's entries for the {prefixes} skills whose pre-renewal entry",
             "differs. Pre-renewal's are an older revision: no Status: (so the buffs",
             "start nothing) and other fields the skill classes no longer match.",
             "A field pre-renewal sets and renewal does not is reset explicitly,",
             "since an import entry only replaces the fields it names. The same goes",
             "for keys inside DamageFlags, Flags and Requires' Ammo and Weapon: those",
             "merge key by key, so a key pre-renewal sets is cleared explicitly.",
             "Fields marked as this mod's own come from SKILL_OVERRIDES in build.py."]
    if C.FIXED_CAST_TO_DELAY is not None:
        about += [f"Pre-renewal has no fixed cast time, so {int(C.FIXED_CAST_TO_DELAY * 100)}% of each skill's renewal",
                  "FixedCastTime is added to its after-cast delay, which DEX does not",
                  "reduce, and the rest to its cast time."]
        if C.FIXED_CAST_COOLDOWN_EXEMPT is not None:
            about += [f"A skill with a cooldown of {C.FIXED_CAST_COOLDOWN_EXEMPT // 1000}s or more cannot be spammed anyway:",
                      "its whole fixed cast goes into its cast time instead."]
    about += [
             "", "Skills: " + ", ".join(changed)]
    if pre_only:
        about += ["", "Not in renewal's skill_db, so pre-renewal's entry is kept: " + ", ".join(pre_only)]
    if added:
        about += ["", "Flags added to other classes' skills (only that key; the rest of", "pre-renewal's entry stays): " + ", ".join(added)]
    return about, "\n".join(out) + "\n"


def read_csv(name):
    with open(C.CSV / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def item_fields(entry):
    g = lambda f: (re.search(r"^    " + f + r": (.+)$", entry, re.M) or [None, None])[1]
    locs = section(entry, "Locations") or []
    return dict(id=int(re.match(r"- Id: (\d+)", entry.strip()).group(1)), aegis=g("AegisName"),
                name=g("Name"), view=g("View"), range=g("Range"),
                locations=[l.split(":")[0].strip() for l in locs if l.strip().endswith("true")])


def build_items(src, iteminfo):
    files = ("db/pre-re/item_db_equip.yml", "db/pre-re/item_db_usable.yml", "db/pre-re/item_db_etc.yml")
    stock = {}
    for f in files:
        for e in body_entries(src[f], "Id"):
            it = item_fields(e)
            stock[it["aegis"]] = (it, e)

    # 1. Everything the base class can wear or use, the new class can too: the
    #    equipment, the ammunition, the class's potions.
    flags = []
    for e in (e for f in files for e in body_entries(src[f], "Id")):
        jobs = entry_jobs(e)
        if C.ITEM_JOB and jobs.get(C.BASE) == "true" and jobs.get("All") != "true" and C.ITEM_JOB not in jobs:
            it = item_fields(e)
            lines = [f"  - Id: {it['id']}    # {it['name']}", "    Jobs:"]
            lines += [f"      {j}: {v}" for j, v in jobs.items()] + [f"      {C.ITEM_JOB}: true"]
            flags.append("\n".join(lines))

    # 2. Renewal's consumables the skills need and pre-renewal lacks, as they are.
    re_items = {}
    for f in ("db/re/item_db_etc.yml", "db/re/item_db_usable.yml"):
        for e in body_entries(src[f], "Id"):
            re_items[item_fields(e)["aegis"]] = e
    for aegis in C.NEW_FROM_RENEWAL:
        if aegis in stock:
            fail(f"{aegis} is in pre-renewal already: drop it from NEW_FROM_RENEWAL")
        if aegis not in re_items:
            fail(f"{aegis} is not in renewal's item tables")
        e = re_items[aegis]
        jobs = entry_jobs(e)
        if C.ITEM_JOB and jobs.get(C.BASE) == "true" and C.ITEM_JOB not in jobs:
            e = re.sub(r"(^    Jobs:\n(?:      .*\n)+)", lambda m: m.group(1) + f"      {C.ITEM_JOB}: true\n", e + "\n", count=1, flags=re.M).rstrip("\n")
        flags.append(e)

    # 2b. Fields this mod sets on stock items (ITEM_FIELDS).
    re_all = {}
    for f in ("db/re/item_db_etc.yml", "db/re/item_db_usable.yml"):
        for e in body_entries(src[f], "Id"):
            re_all[item_fields(e)["aegis"]] = e
    for aegis, fields in C.ITEM_FIELDS.items():
        it, pre_e = stock.get(aegis) or fail(f"ITEM_FIELDS: {aegis} is not a pre-renewal item")
        lines = [f"  - Id: {it['id']}    # {it['name']}: this mod's fields only"]
        for field, value in fields.items():
            if value == "renewal":
                e = re_all.get(aegis) or fail(f"ITEM_FIELDS: renewal has no {aegis}")
                m = re.search(r"^    " + field + r":.*\n(?:      .*\n)*", e + "\n", re.M)
                if not m:
                    fail(f"ITEM_FIELDS: renewal's {aegis} has no {field}")
                first, *rest = m.group(0).rstrip("\n").split("\n")
                lines += [first + "    # renewal's"] + rest
            elif isinstance(value, dict):
                lines.append(f"    {field}:    # this mod's balance")
                lines += [f"      {k}: {v}" for k, v in value.items()]
            else:
                lines.append(f"    {field}: {value}    # this mod's balance")
        flags.append("\n".join(lines))

    # 3. The mod's own equipment.
    rows = read_csv("equipment.csv")
    new, info = [], []
    for r in rows:
        kind = C.KINDS.get(r["kind"]) or fail(f"{r['aegis']}: unknown kind {r['kind']}")
        if r["aegis"] in stock:
            fail(f"{r['aegis']} is already a stock item")
        if not 50000 <= int(r["id"]) <= 99999:
            fail(f"{r['aegis']}: ids for mods are 50000-99999")
        look, _ = stock.get(r["look"]) or fail(f"{r['aegis']}: look {r['look']} is not a pre-renewal item")
        art = iteminfo.get(look["id"]) or fail(f"{r['aegis']}: the translation has no item {look['id']}")
        if not art["res"] or "�" in (art["res"] + (art["unres"] or "")):
            fail(f"{r['aegis']}: item {look['id']}'s resource name did not decode")
        locs = look["locations"] if r["kind"] == "head" else kind["loc"]
        weapon = kind["type"] == "Weapon"

        e = [f"  - Id: {r['id']}", f"    AegisName: {r['aegis']}", f"    Name: {yaml_str(r['name'])}",
             f"    Type: {kind['type']}"]
        if kind["sub"]:
            e.append(f"    SubType: {kind['sub']}")
        e += ["    Buy: 20", f"    Weight: {r['weight']}"]
        e.append(f"    Attack: {r['power']}" if weapon else f"    Defense: {r['power']}")
        if weapon:
            e.append(f"    Range: {look['range'] or 1}")
        if int(r["slots"]):
            e.append(f"    Slots: {r['slots']}")
        e += ["    Jobs:"] + [f"      {j}: true" for j in C.EQUIP_JOBS]
        if C.EQUIP_CLASSES:
            e += ["    Classes:"] + [f"      {k}: true" for k in C.EQUIP_CLASSES]
        e += ["    Locations:"] + [f"      {l}: true" for l in locs]
        if weapon:
            e.append(f"    WeaponLevel: {r['wlv']}")
        else:
            e.append("    ArmorLevel: 1")
        e.append(f"    EquipLevelMin: {r['level']}")
        e.append("    Refineable: true")
        if r["kind"] == "head" or kind.get("view"):   # headgear, and shields: the look's sprite
            if not look["view"]:
                fail(f"{r['aegis']}: look {r['look']} has no View")
            e.append(f"    View: {look['view']}")
        e += ["    Script: |", "      " + r["script"].strip()]
        new.append("\n".join(e))

        desc = r["desc"].split("|")
        lines = [desc[0], RULE] + desc[1:] + [RULE, f"^0000CCType:^000000 {kind['label']}"]
        if weapon:
            lines += [f"^0000CCAttack:^000000 {r['power']}", f"^0000CCWeight:^000000 {int(r['weight']) // 10}",
                      f"^0000CCWeapon Level:^000000 {r['wlv']}"]
        else:
            lines.append(f"^0000CCDefense:^000000 {r['power']}")
            if r["kind"] == "head":
                lines.append("^0000CCPosition:^000000 " + ", ".join(HEAD_POSITION[l] for l in locs))
            lines += [f"^0000CCWeight:^000000 {int(r['weight']) // 10}", "^0000CCArmor Level:^000000 1"]
        lines += [RULE, "^0000CCRequirement:^000000", f"Base Level {r['level']}", C.EQUIP_LABEL or " and ".join(C.JOBS)]
        info.append((r, kind, art, lines))

    combos = read_csv("combos.csv")
    by_aegis = {r["aegis"]: r for r in rows}
    combo_desc = {}
    for c in combos:
        parts = c["items"].split()
        for p in parts:
            if p not in by_aegis:
                fail(f"combo names {p}, which equipment.csv does not have")
        names = [by_aegis[p]["name"] for p in parts]
        for p in parts:
            combo_desc[p] = (names, c["desc"].split("|"))

    about = ([f"1. {C.ITEM_JOB}: true on every pre-renewal item a {C.BASE} can equip or use,",
              "   with the item's other jobs restated (an import entry's Jobs replaces them)."]
             if C.ITEM_JOB else
             [f"1. No job flags: rAthena already lets the class wear a {C.BASE}'s items."]) + [
             ("2. Renewal's " + ", ".join(C.NEW_FROM_RENEWAL) + ", which the skills need."
              if C.NEW_FROM_RENEWAL else "2. No renewal-only items: the skills need none."),
             "3. " + (C.ITEMS_ABOUT or "The mod's equipment, from equipment.csv: four tiers, levels 50-95.")]
    lua = build_iteminfo(info, combo_desc)
    return about, "\n".join(flags + new) + "\n", lua, rows, combos


def wrap_iteminfo(entries):
    out = [f"-- Generated by registry/tools/{C.MOD_NAME}/build.py -- do not hand-edit.",
           f"-- The names, descriptions and art of the {C.MOD_NAME} mod's equipment.",
           "-- The art is borrowed from stock items, by their resource names.",
           "tbl = {"] + entries
    out[-1] = "\t}"
    out.append("}")
    return "\n".join(out) + "\n"


def build_iteminfo(info, combo_desc):
    """The equipment's itemInfo entries, as lines; wrap_iteminfo makes the file."""
    out = []
    q = lambda s: '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    for r, kind, art, lines in info:
        if r["aegis"] in combo_desc:
            names, bonus = combo_desc[r["aegis"]]
            others = [n for n in names if n != r["name"]]
            at = lines.index(RULE, 1 + lines[1:].index(RULE) + 1)  # before the Type block
            add = [RULE, "When equipped with " + ", ".join(f"^990099{n}^000000" for n in others) + ":"] + bonus
            lines = lines[:at] + add + lines[at:]
        out += [f"\t[{r['id']}] = {{",
                f"\t\tunidentifiedDisplayName = {q('Unidentified ' + kind['unid'])},",
                f"\t\tunidentifiedResourceName = {q(art['unres'] or art['res'])},",
                '\t\tunidentifiedDescriptionName = { "Can be identified by using a ^990099Magnifier^000000." },',
                f"\t\tidentifiedDisplayName = {q(r['name'])},",
                f"\t\tidentifiedResourceName = {q(art['res'])},",
                "\t\tidentifiedDescriptionName = {"]
        out += [f"\t\t\t{q(l)}," for l in lines[:-1]] + [f"\t\t\t{q(lines[-1])}"]
        out += ["\t\t},", f"\t\tslotCount = {int(r['slots'])},", f"\t\tClassNum = {art['classnum']}", "\t},"]
    return out


def build_combos(combos):
    out = []
    for c in combos:
        out += ["  - Combos:", "      - Combo:"] + [f"          - {a}" for a in c["items"].split()]
        out += ["    Script: |", "      " + c["script"].strip()]
    if not combos:
        return ["No set bonuses."], "\n".join(out) + "\n"
    return ["The equipment's set bonuses, from combos.csv: mask, garb, scarf and",
            "tabi of one tier."], "\n".join(out) + "\n"


def build_drops(src, rows):
    mobs = {}
    for e in body_entries(src["db/pre-re/mob_db.yml"], "Id"):
        a = re.search(r"^    AegisName: (\S+)", e, re.M).group(1)
        mobs[a] = e
    known = {r["aegis"] for r in rows}
    drops = read_csv("drops.csv")
    out, per_mob = [], {}
    for d in drops:
        if d["item"] not in known:
            fail(f"drops.csv names {d['item']}, which equipment.csv does not have")
        if d["mob"] not in mobs:
            fail(f"drops.csv names {d['mob']}, which pre-renewal's mob_db does not have")
        per_mob.setdefault(d["mob"], []).append(d)
    dropped = {d["item"] for d in drops}
    if known - dropped:
        fail("no monster drops " + ", ".join(sorted(known - dropped)))
    for mob, ds in per_mob.items():
        e = mobs[mob]
        have = len(re.findall(r"^      - Item:", "\n".join(section(e, "Drops") or []), re.M))
        if have + len(ds) > 10:
            fail(f"{mob} has {have} drops; {len(ds)} more is over rAthena's ten")
        mid = re.match(r"- Id: (\d+)", e.strip()).group(1)
        name = re.search(r"^    Name: (.+)$", e, re.M).group(1)
        out += [f"  - Id: {mid}    # {name} ({mob}), {have} stock drops", "    Drops:"]
        for d in ds:
            out += [f"      - Item: {d['item']}", f"        Rate: {d['rate']}"]
    return ["Where the equipment drops, from drops.csv. No Index:, so each is",
            "appended to the monster's own drops; every monster here has room."], "\n".join(out) + "\n"


# ---------------------------------------------------------------- main

def build_class(src, iteminfo, lua):
    """One class's (about, body) for each table; its itemInfo entries go to lua."""
    out = {}
    out["db/job_stats.yml"] = build_job_stats(src)
    out["db/skill_tree.yml"] = build_skill_tree(src)
    out["db/skill_db.yml"] = build_skill_db(src)
    about, body, entries, rows, combos = build_items(src, iteminfo)
    # Every item a shipped skill entry names must exist, or rAthena drops the entry.
    known = {item_fields(e)["aegis"] for f in ("db/pre-re/item_db_equip.yml", "db/pre-re/item_db_usable.yml",
                                                "db/pre-re/item_db_etc.yml") for e in body_entries(src[f], "Id")}
    known |= set(C.NEW_FROM_RENEWAL)
    skill_text = out["db/skill_db.yml"][1]
    named = set(re.findall(r"^        - Item: (\S+)", skill_text, re.M))
    for block in re.findall(r"^      Equipment:\n((?:        \w+: true\n)+)", skill_text, re.M):
        named |= set(re.findall(r"(\w+): true", block))
    missing = sorted(n for n in named if n not in known and not n[0].isdigit())
    if missing:
        fail("skill entries name items pre-renewal lacks: " + ", ".join(missing) + " -- add them to NEW_FROM_RENEWAL")
    out["db/item_db.yml"] = (about, body)
    lua += entries
    out["db/item_combos.yml"] = build_combos(combos)
    out["db/mob_db.yml"] = build_drops(src, rows)
    return out


def run(cfg):
    """Build one mod from its config (see registry/tools/*/build.py), or from a
    list of configs, one per class, into one mod."""
    global C
    cfgs = cfg if isinstance(cfg, list) else [cfg]
    for c in cfgs[1:]:
        if c.MOD_NAME != cfgs[0].MOD_NAME or c.ROOT != cfgs[0].ROOT:
            sys.exit("build.py: every class config must name the same mod")
    C = cfgs[0]
    ap = argparse.ArgumentParser(description=f"Regenerate the {C.MOD_NAME} mod's tables.")
    ap.add_argument("--rathena", type=Path, default=C.ROOT / "vendor" / "rathena")
    ap.add_argument("--commit", default=None, help="default: the pin in config/VENDOR_PINS")
    ap.add_argument("--check", action="store_true", help="fail if a generated file is stale")
    args = ap.parse_args()

    commit = args.commit or pinned_commit()
    paths = ["db/pre-re/job_stats.yml", "db/pre-re/job_exp.yml", "db/pre-re/job_basepoints.yml",
             "db/re/job_stats.yml", "db/re/skill_tree.yml", "db/pre-re/skill_db.yml", "db/re/skill_db.yml",
             "db/pre-re/item_db_equip.yml", "db/pre-re/item_db_usable.yml", "db/pre-re/item_db_etc.yml",
             "db/pre-re/mob_db.yml", "db/pre-re/job_aspd.yml", "db/re/item_db_etc.yml", "db/re/item_db_usable.yml"]
    src = {p: git_show(args.rathena, commit, p) for p in paths}
    source = f"rathena {commit}"
    iteminfo = lua_items(C.ITEMINFO)

    # Each class's part of every file; several classes' parts are joined.
    parts, lua, mobs = {}, [], {}
    for cfg in cfgs:
        C = cfg
        for rel, (about, body) in build_class(src, iteminfo, lua).items():
            parts.setdefault(rel, []).append((about, body))
        for mob in re.findall(r"^  - Id: (\d+)", parts["db/mob_db.yml"][-1][1], re.M):
            if mob in mobs:
                fail(f"monster {mob} drops items of two classes: give each class its own monsters")
            mobs[mob] = cfg.JOBS
    kinds = {"db/job_stats.yml": ("JOB_STATS", 4), "db/skill_tree.yml": ("SKILL_TREE_DB", 1),
             "db/skill_db.yml": ("SKILL_DB", 4), "db/item_db.yml": ("ITEM_DB", 3),
             "db/item_combos.yml": ("COMBO_DB", 1), "db/mob_db.yml": ("MOB_DB", 5)}
    outputs = {}
    for rel, (kind, version) in kinds.items():
        if len(cfgs) == 1:
            about = parts[rel][0][0]
        else:
            about = []
            for cfg, (a, _) in zip(cfgs, parts[rel]):
                about += (["", RULE] if about else []) + [", ".join(cfg.JOBS) + ":"] + a
        text = header(kind, version, source, about) + "".join(b for _, b in parts[rel])
        outputs[rel] = text
        if rel == "db/item_db.yml":
            outputs["System/itemInfo.lua"] = wrap_iteminfo(lua)

    stale = []
    for rel, text in outputs.items():
        path = C.MOD / rel
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        fail("stale: " + ", ".join(stale) + " -- rerun build.py")
    print(("checked " if args.check else "wrote ") + ", ".join(outputs))

