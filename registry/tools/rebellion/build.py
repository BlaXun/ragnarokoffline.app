#!/usr/bin/env python3
"""Regenerate the rebellion mod's tables from rAthena and three CSV files.

A development tool, run by whoever updates the mod -- never by the app. The mod
is the generated files, committed; nothing a player installs runs Python.

    python3 registry/tools/rebellion/build.py            # rewrite them
    python3 registry/tools/rebellion/build.py --check    # fail if stale

It reads rAthena's tables at the commit config/VENDOR_PINS pins, with
`git show <commit>:<path>`, from the checkout `--rathena` names (default:
vendor/rathena; a fork checkout beside this repo works too). Item art comes
from the English translation's item table in vendor/ROenglishRE.

What it writes, under registry/mods/rebellion/:

  db/job_stats.yml    Rebellion, which pre-renewal's tables lack: HP/SP per
                      level, EXP tables, job bonuses, ASPD, weight.
  db/skill_tree.yml   renewal's Rebellion tree, unchanged.
  db/skill_db.yml     renewal's entries for every RL_ skill whose pre-renewal
                      entry differs. Pre-renewal's are an older revision with
                      no `Status:` (so Platinum Alter, Heat Barrel and the
                      other buffs would start nothing).
  db/item_db.yml      `Rebellion: true` on every pre-renewal item a Gunslinger
                      can wear or use, renewal's ammunition items that
                      pre-renewal lacks, and the mod's own equipment
                      (equipment.csv).
  db/item_combos.yml  the equipment's set bonuses (combos.csv).
  db/mob_db.yml       where the equipment drops (drops.csv).
  System/itemInfo.lua the equipment's names, descriptions and art.

The NPCs (npc/) and the skill damage hooks (lua/) are written by hand.
docs/mods/EXPANDED_CLASS_REBIRTH.md is the guide this follows.

Standard library only. The stock tables are regular enough to read line by
line; a shape this does not recognise is an error, not a shorter output.
"""

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = Path(__file__).resolve().parent
MOD = ROOT / "registry" / "mods" / "rebellion"
ITEMINFO = ROOT / "vendor" / "ROenglishRE" / "Translation" / "Renewal" / "SystemEN" / "LuaFiles514" / "itemInfo.lua"

JOBS = ("Rebellion",)
ITEM_JOB = "Rebellion"        # the item_db Jobs: key (EAJ_REBELLION)
BASE = "Gunslinger"           # the class one changes from
SKILL_PREFIX = "RL_"
MOD_NAME = "rebellion"

# Rebellion sits a little below a transcendent class. Pre-renewal's Sniper
# gets the Hunter HP table times 1.25; Rebellion gets it times 1.1. SP follows
# the Gunslinger's table.
HP_FROM, HP_SCALE = "Sniper", 1.10
SP_FROM, SP_SCALE = "Gunslinger", 1.10
EXP_FROM = "Sniper"           # transcendent base and second-job EXP tables

# Renewal's job bonuses come to +37 by job 60. These three more make +40,
# five below a transcendent class's +45.
EXTRA_BONUS = [(56, "Dex"), (58, "Agi"), (60, "Luk")]
BONUS_TOTAL = 40

MAX_JOB_LEVEL = 60

# Renewal's skills consume these, and pre-renewal's item tables do not have
# them. They are added under their renewal ids, which the client already knows.
# Sanctified_Bullet and Silver_Bullet_ are bullets Platinum Alter names as
# required equipment; one missing item makes rAthena reject the whole entry.
NEW_FROM_RENEWAL = ["Full_Metal_Jacket", "Shooting_Mine", "Dragon_Tail_Missile", "Slug_Bullet",
                    "Sanctified_Bullet", "Silver_Bullet_"]

# What each kind of equipment is, for item_db and the description.
KINDS = {
    "revolver":  dict(type="Weapon", sub="Revolver", loc=["Right_Hand"],  label="Revolver",         unid="Gun"),
    "rifle":     dict(type="Weapon", sub="Rifle",    loc=["Both_Hand"],   label="Rifle",            unid="Gun"),
    "gatling":   dict(type="Weapon", sub="Gatling",  loc=["Both_Hand"],   label="Gatling Gun",      unid="Gun"),
    "shotgun":   dict(type="Weapon", sub="Shotgun",  loc=["Both_Hand"],   label="Shotgun",          unid="Gun"),
    "grenade":   dict(type="Weapon", sub="Grenade",  loc=["Both_Hand"],   label="Grenade Launcher", unid="Gun"),
    "head":      dict(type="Armor",  sub=None,     loc=None,               label="Headgear",       unid="Hat"),
    "armor":     dict(type="Armor",  sub=None,     loc=["Armor"],          label="Armor",          unid="Armor"),
    "garment":   dict(type="Armor",  sub=None,     loc=["Garment"],        label="Garment",        unid="Garment"),
    "shoes":     dict(type="Armor",  sub=None,     loc=["Shoes"],          label="Shoes",          unid="Shoes"),
    "accessory": dict(type="Armor",  sub=None,     loc=["Both_Accessory"], label="Accessory",      unid="Accessory"),
}
HEAD_POSITION = {"Head_Top": "Upper", "Head_Mid": "Middle", "Head_Low": "Lower"}

RULE = "_______________________"


def fail(msg):
    sys.exit(f"build.py: {msg}")


# ---------------------------------------------------------------- reading

def pinned_commit():
    for line in (ROOT / "config" / "VENDOR_PINS").read_text().splitlines():
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
    lines = ["# Generated by registry/tools/rebellion/build.py -- do not",
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

    renewal = job_block(re_stats, JOBS[0], "BonusStats")
    bonus = re.findall(r"- Level: (\d+)\n((?:\s{8}\w+: -?\d+\n?)+)", "\n".join(section(renewal, "BonusStats")) + "\n")
    bonus = [(int(l), st, int(v)) for l, body in bonus for st, v in re.findall(r"(\w+): (-?\d+)", body)
             if int(l) <= MAX_JOB_LEVEL]
    bonus += [(l, st, 1) for l, st in EXTRA_BONUS]
    if sum(v for _, _, v in bonus) != BONUS_TOTAL:
        fail(f"job bonuses add up to {sum(v for _, _, v in bonus)}, not {BONUS_TOTAL}: adjust EXTRA_BONUS")

    base_exp = job_block(exp, EXP_FROM, "BaseExp")
    max_base = re.search(r"^    MaxBaseLevel: (\d+)", base_exp, re.M).group(1)
    job_exp = job_block(exp, EXP_FROM, "JobExp")
    job_levels = [(l, v) for l, v in level_values(section(job_exp, "JobExp"), "Exp") if l < MAX_JOB_LEVEL]
    if len(job_levels) != MAX_JOB_LEVEL - 1:
        fail("the transcendent job EXP table is shorter than expected")

    hp = level_values(section(job_block(points, HP_FROM, "BaseHp"), "BaseHp"), "Hp")
    sp = level_values(section(job_block(points, SP_FROM, "BaseSp"), "BaseSp"), "Sp")
    base_stats = job_block(stats, BASE, "BonusStats")
    weight = re.search(r"^    MaxWeight: (\d+)", base_stats, re.M).group(1)
    hp_factor = re.search(r"^    HpFactor: (\d+)", base_stats, re.M).group(1)
    sp_increase = (re.search(r"^    SpIncrease: (\d+)", base_stats, re.M) or [None, "100"])[1]
    aspd = section(job_block(body_entries(src["db/pre-re/job_aspd.yml"], "Jobs"), BASE, "BaseASPD"), "BaseASPD")

    jobs = ["  - Jobs:"] + [f"      {j}: true" for j in JOBS]
    out = list(jobs)
    out += [f"    MaxWeight: {weight}", f"    HpFactor: {hp_factor}", f"    SpIncrease: {sp_increase}", "    BaseASPD:"]
    out += aspd
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
    out += [f"    MaxJobLevel: {MAX_JOB_LEVEL}", "    JobExp:"]
    for lvl, val in job_levels:
        out += [f"      - Level: {lvl}", f"        Exp: {val}"]
    out += ["    BaseHp:"]
    for lvl, val in hp:
        out += [f"      - Level: {lvl}", f"        Hp: {round(val * HP_SCALE)}"]
    out += ["    BaseSp:"]
    for lvl, val in sp:
        out += [f"      - Level: {lvl}", f"        Sp: {round(val * SP_SCALE)}"]

    totals = {}
    for _, s, v in bonus:
        totals[s] = totals.get(s, 0) + v
    about = [
        f"{', '.join(JOBS)}, which pre-renewal's job tables do not have.",
        f"Base levels 1-{max_base} on the transcendent EXP table, job levels",
        f"1-{MAX_JOB_LEVEL} on the transcendent second-job table (cut at {MAX_JOB_LEVEL}).",
        f"HP: {HP_FROM} x {HP_SCALE}. SP: {SP_FROM} x {SP_SCALE}. ASPD and weight: the {BASE}'s.",
        f"Job bonuses: renewal's to job {MAX_JOB_LEVEL}, then one each at "
        + ", ".join(str(l) for l, _ in EXTRA_BONUS) + f" (+{sum(totals.values())} in all).",
    ]
    return about, "\n".join(out) + "\n"


def build_skill_tree(src):
    tree = body_entries(src["db/re/skill_tree.yml"], "Job")
    out = [e for e in tree if e.split("\n")[0].strip() in [f"- Job: {j}" for j in JOBS]]
    if len(out) != len(JOBS):
        fail(f"renewal's skill tree lacks one of {JOBS}")
    return [f"Renewal's {', '.join(JOBS)} tree, unchanged. It inherits Novice and",
            f"{BASE}, so every point earned after the change can also go into {BASE} skills."], \
        "\n".join(out) + "\n"


# Fields this mod sets differently from both eras, for pre-renewal's balance.
# Each needs a reason beside it; see docs/mods/EXPANDED_CLASS_REBIRTH.md §7.
SKILL_OVERRIDES = {
}

SKILL_DEFAULTS = {"Element": "Neutral", "Range": "0", "AfterCastActDelay": "0", "AfterCastWalkDelay": "0", "Duration1": "0",
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


def build_skill_db(src):
    pre = by_field(body_entries(src["db/pre-re/skill_db.yml"], "Id"), "Name")
    ren = by_field(body_entries(src["db/re/skill_db.yml"], "Id"), "Name")
    names = sorted(n for n in pre if n.startswith(SKILL_PREFIX))
    out, changed = [], []
    for n in names:
        if n not in ren:
            fail(f"{n} is not in renewal's skill_db")
        if pre[n] == ren[n]:
            continue
        keys = lambda e: set(re.findall(r"^    (\w+):", e, re.M))
        dropped = keys(pre[n]) - keys(ren[n])
        entry = ren[n]
        for k in sorted(dropped):
            if k not in SKILL_DEFAULTS:
                fail(f"{n}: pre-renewal sets {k}, renewal does not, and there is no reset value for it")
            entry += f"\n    {k}: {SKILL_DEFAULTS[k]}    # pre-renewal's entry sets this; renewal's does not"
        entry = nested_resets(n, pre[n], entry)
        for k, v in SKILL_OVERRIDES.get(n, {}).items():
            line = re.compile(r"^    " + k + r":.*$", re.M)
            if not line.search(entry):
                fail(f"{n}: no {k} to override")
            entry = line.sub(f"    {k}: {v}    # this mod's balance; renewal's is different", entry)
        out.append(entry)
        changed.append(n)
    about = [f"Renewal's entries for the {SKILL_PREFIX} skills whose pre-renewal entry",
             "differs. Pre-renewal's are an older revision: no Status: (so the buffs",
             "start nothing) and other fields the skill classes no longer match.",
             "A field pre-renewal sets and renewal does not is reset explicitly,",
             "since an import entry only replaces the fields it names. The same goes",
             "for keys inside DamageFlags, Flags and Requires' Ammo and Weapon: those",
             "merge key by key, so a key pre-renewal sets is cleared explicitly.",
             "Fields marked as this mod's own come from SKILL_OVERRIDES in build.py.",
             "", "Skills: " + ", ".join(changed)]
    return about, "\n".join(out) + "\n"


def read_csv(name):
    with open(TOOL / name, newline="", encoding="utf-8") as f:
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
        if jobs.get(BASE) == "true" and jobs.get("All") != "true" and ITEM_JOB not in jobs:
            it = item_fields(e)
            lines = [f"  - Id: {it['id']}    # {it['name']}", "    Jobs:"]
            lines += [f"      {j}: {v}" for j, v in jobs.items()] + [f"      {ITEM_JOB}: true"]
            flags.append("\n".join(lines))

    # 2. Renewal's consumables the skills need and pre-renewal lacks, as they are.
    re_items = {}
    for f in ("db/re/item_db_etc.yml", "db/re/item_db_usable.yml"):
        for e in body_entries(src[f], "Id"):
            re_items[item_fields(e)["aegis"]] = e
    for aegis in NEW_FROM_RENEWAL:
        if aegis in stock:
            fail(f"{aegis} is in pre-renewal already: drop it from NEW_FROM_RENEWAL")
        if aegis not in re_items:
            fail(f"{aegis} is not in renewal's item tables")
        e = re_items[aegis]
        jobs = entry_jobs(e)
        if jobs.get(BASE) == "true" and ITEM_JOB not in jobs:
            e = re.sub(r"(^    Jobs:\n(?:      .*\n)+)", lambda m: m.group(1) + f"      {ITEM_JOB}: true\n", e + "\n", count=1, flags=re.M).rstrip("\n")
        flags.append(e)

    # 3. The mod's own equipment.
    rows = read_csv("equipment.csv")
    new, info = [], []
    for r in rows:
        kind = KINDS.get(r["kind"]) or fail(f"{r['aegis']}: unknown kind {r['kind']}")
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
        e += ["    Jobs:", f"      {ITEM_JOB}: true", "    Locations:"] + [f"      {l}: true" for l in locs]
        if weapon:
            e.append(f"    WeaponLevel: {r['wlv']}")
        else:
            e.append("    ArmorLevel: 1")
        e.append(f"    EquipLevelMin: {r['level']}")
        e.append("    Refineable: true")
        if r["kind"] == "head":
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
        lines += [RULE, "^0000CCRequirement:^000000", f"Base Level {r['level']}", " and ".join(JOBS)]
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

    about = [f"1. {ITEM_JOB}: true on every pre-renewal item a {BASE} can equip or use,",
             "   with the item's other jobs restated (an import entry's Jobs replaces them).",
             "2. Renewal's " + ", ".join(NEW_FROM_RENEWAL) + ", which the skills consume.",
             "3. The mod's equipment, from equipment.csv: four tiers, levels 50-95."]
    lua = build_iteminfo(info, combo_desc)
    return about, "\n".join(flags + new) + "\n", lua, rows, combos


def build_iteminfo(info, combo_desc):
    out = [f"-- Generated by registry/tools/{MOD_NAME}/build.py -- do not hand-edit.",
           f"-- The names, descriptions and art of the {MOD_NAME} mod's equipment.",
           "-- The art is borrowed from stock items, by their resource names.",
           "tbl = {"]
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
    out[-1] = "\t}"
    out.append("}")
    return "\n".join(out) + "\n"


def build_combos(combos):
    out = []
    for c in combos:
        out += ["  - Combos:", "      - Combo:"] + [f"          - {a}" for a in c["items"].split()]
        out += ["    Script: |", "      " + c["script"].strip()]
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

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rathena", type=Path, default=ROOT / "vendor" / "rathena")
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
    iteminfo = lua_items(ITEMINFO)

    outputs = {}
    about, body = build_job_stats(src)
    outputs["db/job_stats.yml"] = header("JOB_STATS", 4, source, about) + body
    about, body = build_skill_tree(src)
    outputs["db/skill_tree.yml"] = header("SKILL_TREE_DB", 1, source, about) + body
    about, body = build_skill_db(src)
    outputs["db/skill_db.yml"] = header("SKILL_DB", 4, source, about) + body
    about, body, lua, rows, combos = build_items(src, iteminfo)
    # Every item a shipped skill entry names must exist, or rAthena drops the entry.
    known = {item_fields(e)["aegis"] for f in ("db/pre-re/item_db_equip.yml", "db/pre-re/item_db_usable.yml",
                                                "db/pre-re/item_db_etc.yml") for e in body_entries(src[f], "Id")}
    known |= set(NEW_FROM_RENEWAL)
    skill_text = outputs["db/skill_db.yml"]
    named = set(re.findall(r"^        - Item: (\S+)", skill_text, re.M))
    for block in re.findall(r"^      Equipment:\n((?:        \w+: true\n)+)", skill_text, re.M):
        named |= set(re.findall(r"(\w+): true", block))
    missing = sorted(n for n in named if n not in known and not n[0].isdigit())
    if missing:
        fail("skill entries name items pre-renewal lacks: " + ", ".join(missing) + " -- add them to NEW_FROM_RENEWAL")
    outputs["db/item_db.yml"] = header("ITEM_DB", 3, source, about) + body
    outputs["System/itemInfo.lua"] = lua
    about, body = build_combos(combos)
    outputs["db/item_combos.yml"] = header("COMBO_DB", 1, source, about) + body
    about, body = build_drops(src, rows)
    outputs["db/mob_db.yml"] = header("MOB_DB", 5, source, about) + body

    stale = []
    for rel, text in outputs.items():
        path = MOD / rel
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        fail("stale: " + ", ".join(stale) + " -- rerun build.py")
    print(("checked " if args.check else "wrote ") + ", ".join(outputs))


if __name__ == "__main__":
    main()
