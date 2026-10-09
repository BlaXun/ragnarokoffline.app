#!/usr/bin/env python3
"""Regenerate registry/mods/pre-renewal-spawns/npc/ from rAthena's spawn scripts.

A development tool, run by whoever updates the mod -- never by the app. The
mod ships the generated scripts, committed; nothing a player installs runs
Python. It lives outside the mod folder because the registry index does not
carry .py files.

    python3 registry/tools/pre-renewal-spawns/build_spawns.py            # rewrite them
    python3 registry/tools/pre-renewal-spawns/build_spawns.py --check    # fail if stale

By default it reads vendor/rathena, which should be the commit
config/VENDOR_PINS names (`scripts/vendor-fetch.sh rathena vendor/rathena`).
`--source` reads another copy instead.

What it writes:

  npc/pre-re/...   every file npc/pre-re/scripts_monsters.conf loads, as it
                   is, minus any line naming a monster the renewal mob_db
                   does not have.
  npc/re/...       for each renewal spawn file that spawns on a pre-renewal
                   map: what is left of it once those maps are taken out, so
                   the maps pre-renewal never had keep their renewal spawns.
  npc/pre_renewal_spawns.txt
                   the script that unloads those renewal files once the server
                   is up, and tidies after the scripts they held.

A "pre-renewal map" is one with a spawn line in the pre-renewal files. Both
eras load the same map list, so this is the only line between them that the
sources draw. npc/scripts_monsters.conf (jail, pvp, towns) is loaded in both
eras and left alone. Standard library only.
"""

import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
MOD = "pre-renewal-spawns"
OUTPUT = os.path.join(REPO, "registry", "mods", MOD, "npc")
CONTROLLER = "pre_renewal_spawns.txt"

# <map>{,<x>,<y>{,<xs>,<ys>}}<TAB>monster|boss_monster|miniboss_monster<TAB><name>{,<level>}<TAB><id>,<amount>...
SPAWN = re.compile(r"^([^\t,]+)(?:,[^\t]*)?\t(?:boss_|miniboss_)?monster\t[^\t]*\t\s*(\w+)\s*,\s*\d+")
# <map>,<x>,<y>,<facing><TAB>script<TAB><name><TAB>... or -<TAB>script<TAB><name><TAB>...
SCRIPT = re.compile(r"^([^\t,]+)(?:,[^\t]*)?\tscript\t([^\t]+)\t")
MONSTER_CALL = re.compile(r"\b(?:area)?monster\s*\(?\s*\"([^\"]+)\"")
NPC_LINE = re.compile(r"^npc:\s*(\S+)")
MOB_ID = re.compile(r"^\s+- Id:\s*(\d+)")
MOB_AEGIS = re.compile(r"^\s+AegisName:\s*(\S+)")
MAP_LINE = re.compile(r"^map:\s*(\S+)")


def read(path):
    # rAthena's scripts are not all UTF-8; latin-1 round-trips every byte.
    with open(path, encoding="latin-1", newline="") as f:
        return f.read()


def script_list(source, conf):
    text = read(os.path.join(source, conf))
    return [m.group(1) for line in text.splitlines() if (m := NPC_LINE.match(line.strip()))]


class Entry:
    """One thing a script file defines: a spawn line or a whole script block."""

    def __init__(self, kind, map_name, first, last, name=None, mob=None):
        self.kind, self.map, self.first, self.last = kind, map_name, first, last
        self.name, self.mob = name, mob

    def unique_name(self):
        return self.name.split("::", 1)[1] if "::" in self.name else self.name


def parse(text, path):
    """The spawn lines and script blocks of a file, by line number, skipping comments."""
    lines = text.split("\n")
    entries, in_comment, i = [], False, 0
    while i < len(lines):
        line = lines[i].rstrip("\r")
        starts_in_comment = in_comment
        # Track /* */ across lines; a line that opens one is inert from there on.
        code = line.split("//", 1)[0]
        pos = 0
        while True:
            if in_comment:
                end = code.find("*/", pos)
                if end < 0:
                    break
                in_comment, pos = False, end + 2
            else:
                start = code.find("/*", pos)
                if start < 0:
                    break
                in_comment, pos = True, start + 2
        if starts_in_comment:
            i += 1
            continue
        code = re.sub(r"/\*.*", "", code).rstrip()
        if m := SPAWN.match(code):
            entries.append(Entry("spawn", m.group(1), i, i, mob=m.group(2)))
        elif m := SCRIPT.match(code):
            end = next((j for j in range(i + 1, len(lines)) if lines[j].startswith("}")), None)
            if end is None:
                sys.exit(f"{path}:{i + 1}: script {m.group(2)} has no closing brace at the start of a line")
            entries.append(Entry("script", m.group(1), i, end, name=m.group(2)))
            i = end
        elif code.strip() and not starts_in_comment:
            sys.exit(f"{path}:{i + 1}: not a spawn line or a script, which this tool does not know how to "
                     f"carry over: {code.strip()[:80]}")
        i += 1
    return lines, entries


def body(lines, entry):
    return "\n".join(lines[entry.first:entry.last + 1])


def has_oninit(lines, entry):
    return entry.kind == "script" and re.search(r"^OnInit\s*:", body(lines, entry), re.M) is not None


def spawn_maps(lines, entry):
    """The maps a script summons monsters on, so far as its source says."""
    maps = set(MONSTER_CALL.findall(body(lines, entry)))
    if entry.map != "-":
        maps.add(entry.map)
    return maps


def mob_db(source):
    ids, names = set(), set()
    for line in read(os.path.join(source, "db/re/mob_db.yml")).splitlines():
        if m := MOB_ID.match(line):
            ids.add(m.group(1))
        elif m := MOB_AEGIS.match(line):
            names.add(m.group(1))
    return ids, names


def source_commit(source):
    try:
        return subprocess.run(["git", "-C", source, "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def header(what, commit):
    return (f"//===== {MOD} ====================================================\n"
            f"//= {what}\n"
            f"//= Generated by registry/tools/{MOD}/build_spawns.py from rAthena\n"
            f"//= {commit}. Do not edit by hand; rerun the script.\n"
            f"//=================================================================\n")


def tidy(lines):
    """Drop runs of blank lines left where entries were taken out."""
    out = []
    for line in lines:
        if not line.strip() and out and not out[-1].strip():
            continue
        out.append(line)
    return "\n".join(out).strip("\n") + "\n"


def build(source):
    commit = source_commit(source)
    pre_files = script_list(source, "npc/pre-re/scripts_monsters.conf")
    re_files = script_list(source, "npc/re/scripts_monsters.conf")
    if not pre_files or not re_files:
        sys.exit(f"no spawn scripts listed under {source}/npc -- is --source an rAthena checkout?")
    ids, aegis = mob_db(source)
    maps = {m.group(1) for line in read(os.path.join(source, "conf/maps_athena.conf")).splitlines()
            if (m := MAP_LINE.match(line.strip()))}

    pre = {rel: parse(read(os.path.join(source, rel)), rel) for rel in pre_files}
    pre_maps = {e.map for _, entries in pre.values() for e in entries if e.kind == "spawn"}

    files, stats = {}, {"pre_lines": 0, "dropped": [], "unloaded": [], "kept_lines": 0}
    mod_scripts = []  # (lines, entry) for every script this mod loads

    for rel, (lines, entries) in pre.items():
        out = list(lines)
        for e in entries:
            if e.kind == "script":
                mod_scripts.append((lines, e))
                continue
            known = e.mob in ids or e.mob in aegis
            if known and e.map in maps:
                stats["pre_lines"] += 1
                continue
            why = f"monster {e.mob} is not in the renewal mob_db" if not known else f"map {e.map} is not loaded"
            stats["dropped"].append(f"{rel}:{e.first + 1}: {why}")
            out[e.first] = f"// {MOD}: left out, {why}: {lines[e.first]}"
        target = "pre-re/" + rel.removeprefix("npc/pre-re/mobs/")
        files[target] = header("Pre-renewal spawns, as the pre-renewal server loads them.", commit) + "\n" + tidy(out)

    clear_maps, stock_inits = set(), []
    for rel in re_files:
        lines, entries = parse(read(os.path.join(source, rel)), rel)
        taken = [e for e in entries if e.map in pre_maps]
        if not taken:
            continue  # nothing on a pre-renewal map: the stock file stays loaded
        stats["unloaded"].append(rel)
        for e in entries:
            if has_oninit(lines, e):
                # Its OnInit ran before the unload, and what it summoned outlives it.
                clear_maps |= spawn_maps(lines, e)
        kept = [e for e in entries if e not in taken]
        if not kept:
            continue
        removed = {i for e in taken for i in range(e.first, e.last + 1)}
        out = [line for i, line in enumerate(lines) if i not in removed]
        mod_scripts += [(lines, e) for e in kept if e.kind == "script"]
        stats["kept_lines"] += sum(1 for e in kept if e.kind == "spawn")
        target = "re/" + rel.removeprefix("npc/re/mobs/")
        files[target] = header(f"What {rel} spawns on maps pre-renewal never had.", commit) + "\n" + tidy(out)

    restart = sorted({e.unique_name() for lines, e in mod_scripts
                      if has_oninit(lines, e) and spawn_maps(lines, e) & clear_maps})

    script = [header("Swaps the renewal spawns for pre-renewal ones on the maps both eras have.", commit),
              "-\tscript\tpre_renewal_spawns\t-1,{",
              "\tend;",
              "",
              "OnInit:",
              "\t// Once every OnInit has run. A file unloaded during that pass would",
              "\t// leave it to chance whether its scripts' OnInit had run yet.",
              "\tsleep 1;",
              "",
              "\t// These files spawn on pre-renewal maps. What they spawn on maps",
              "\t// pre-renewal never had is in this mod's npc/re/, already loaded.",
              "\t// Their scripts loaded after this mod's copies, under new names, and",
              "\t// go with them.",
              *[f"\tatcommand \"@unloadnpcfile {rel}\";" for rel in stats["unloaded"]],
              "",
              "\t// An unloaded script's summoned monsters stay behind...",
              *[f"\tkillmonster \"{m}\",\"All\";" for m in sorted(clear_maps)],
              "\t// ...so the scripts that summon on those maps start over.",
              *[f"\tdonpcevent \"{name}::OnInit\";" for name in restart],
              "",
              f"\tdebugmes \"{MOD}: replaced {len(stats['unloaded'])} renewal spawn files\";",
              "\tend;",
              "}"]
    files[CONTROLLER] = "\n".join(script) + "\n"
    return files, stats, pre_maps


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--source", default=os.path.join(REPO, "vendor", "rathena"))
    parser.add_argument("--check", action="store_true", help="fail if the committed scripts are stale")
    args = parser.parse_args()

    files, stats, pre_maps = build(args.source)

    existing = set()
    for root, _, names in os.walk(OUTPUT):
        for name in names:
            existing.add(os.path.relpath(os.path.join(root, name), OUTPUT).replace(os.sep, "/"))

    if args.check:
        stale = sorted(p for p, text in files.items()
                       if not os.path.exists(os.path.join(OUTPUT, p)) or read(os.path.join(OUTPUT, p)) != text)
        stale += sorted(existing - set(files))
        if stale:
            sys.exit("stale: " + ", ".join(stale) + f"\nrun python3 registry/tools/{MOD}/build_spawns.py")
        print(f"{MOD}: up to date")
        return

    for path in existing - set(files):
        os.remove(os.path.join(OUTPUT, path))
    for path, text in files.items():
        full = os.path.join(OUTPUT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="latin-1", newline="\n") as f:
            f.write(text)

    print(f"{len(pre_maps)} pre-renewal maps, {stats['pre_lines']} pre-renewal spawn lines")
    print(f"{len(stats['unloaded'])} renewal files replaced, {stats['kept_lines']} of their lines kept "
          f"for maps pre-renewal never had")
    for line in stats["dropped"]:
        print(f"left out: {line}")


if __name__ == "__main__":
    main()
