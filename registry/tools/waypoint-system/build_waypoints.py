#!/usr/bin/env python3
"""Build the waypoint-system mod's scripts from rAthena's own data.

Reads waypoints.csv (the curated waypoints) and towns.csv (where the Waypoint
Keepers stand) and an rAthena checkout, and works out for each era what every
waypoint costs to use, what it takes to unlock, and where its board stands.

    python3 build_waypoints.py                  print the table for both eras
    python3 build_waypoints.py --preview x.csv  also write it as a CSV, for review
    python3 build_waypoints.py --write          write the mod's generated scripts
    python3 build_waypoints.py --fill-spots     suggest a board spot for new rows

--rathena (or RATHENA_DIR) points at the checkout; the default is the app's
vendor/rathena. Python 3, no packages. Nothing here runs in the game.
"""
import argparse
import collections
import csv
import glob
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../.."))
MOD = os.path.join(ROOT, "registry/mods/waypoint-system")
# Where each era's generated script goes. Renewal is the mod's own npc/, and
# the pre-re folder (mod.json "prerenewalFolder") replaces it in pre-renewal.
OUT = {"re": "npc/waypoints_placed.txt", "pre-re": "pre-re/npc/waypoints_placed.txt"}

# --- Balance knobs -----------------------------------------------------------
# Fee: the larger of a distance price (maps from the nearest town) and a level
# price, plus a surcharge per dungeon floor below the first, rounded to 50.
FEE_BASE, FEE_PER_HOP = 300, 250
FEE_PER_LEVEL = {"Field": 15, "Dungeon": 30}
FEE_PER_FLOOR = 300
FEE_CAP = 5000
# Unlock: roughly how many kills on the map the items should take.
BUDGET = {("Field", False): 60, ("Field", True): 120,
          ("Dungeon", False): 150, ("Dungeon", True): 250}
HIGH_BAND = {"pre-re": 66, "re": 111}    # average mob level that counts as "high"
COMMON_MIN = 0.02                        # expected drops per kill to count as common
UNCOMMON = (50, 500)                     # per-drop rate (of 10000) for the uncommon pick
UNCOMMON_MIN_SHARE = 0.15                # ...from a mob that is this share of the map
QTY_COMMON = (5, 100)
QTY_UNCOMMON = (1, 10)
SERVER_DROP_RATE = 1.0                   # conf/battle/drops.conf item_rate_common / 100
# Generic items found everywhere and worth more than the unlock: refine ores and
# gemstones. Never asked for.
EXCLUDE_ITEMS = {"Elunium", "Oridecon", "Elunium_Stone", "Oridecon_Stone",
                 "Red_Gemstone", "Blue_Gemstone", "Yellow_Gemstone"}
PLANT_AI = {"06"}                        # plants' drops do not count

# --- Map graph ---------------------------------------------------------------
# Scripts whose warps are not a player's way into a map.
SKIP_SCRIPTS = re.compile(r"custom|events|instances|CashShop|kafras|guides|eden|warper|test|jobs/|achievements|adven_boards")
NOISE_TOWNS = {"-", "bat_room", "turbo_room", "job3_rune01", "lhz_in02", "moc_para01",
               "alb2trea", "izlu2dun", "pay_arche", "prt_fild05", "moc_ruins", "glast_01"}
# Kafra teleport destinations that are not towns, and towns served by other
# teleport services.
KAFRA_EXTRA = {"cmd_fild07", "mjolnir_02", "gef_fild10", "izlude", "dicastes01"}
# Ways in that the script scan misses (the NPC is defined on "-" and duplicated).
MANUAL_EDGES = [("izlude", "izlu2dun", None, None)]

# --- Board placement ---------------------------------------------------------
BOARD_RING = (3, 8)        # cells from where you walk onto the map
BOARD_KEEP_CLEAR = 3       # cells from any warp portal or other NPC


def npc_files(rathena, era):
    confs = [c for c in glob.glob(f"{rathena}/npc/scripts_*.conf") + glob.glob(f"{rathena}/npc/{era}/scripts_*.conf")
             if "custom" not in c and "test" not in c]
    files, dels = [], set()
    for c in confs:
        for line in open(c, errors="ignore"):
            m = re.match(r"(npc|delnpc):\s*(\S+)", line.split("//")[0].strip())
            if m:
                (dels.add if m.group(1) == "delnpc" else files.append)(m.group(2))
    return [f for f in files if f not in dels and os.path.exists(f"{rathena}/{f}")]


class World:
    """The parts of an era's NPC scripts the generator needs."""

    def __init__(self, rathena, era):
        self.edges = collections.defaultdict(set)
        self.walk_edges = collections.defaultdict(set)  # warps only, plus boats and sailors from town
        script_edges = []
        self.arrivals = collections.defaultdict(list)   # map -> [(from map, x, y)]
        self.portals = collections.defaultdict(list)    # map -> [(x, y)] warp portals on it
        self.npcs = collections.defaultdict(list)       # map -> [(x, y)] NPCs standing on it
        self.spawns = collections.defaultdict(list)
        self.dungeon_maps, self.shop_items, kafra = set(), set(), set()
        for f in npc_files(rathena, era):
            script_ok = not SKIP_SCRIPTS.search(f)
            is_dungeon_spawn = "/mobs/dungeons/" in f
            cur = None
            for line in open(f"{rathena}/{f}", errors="ignore"):
                if line.startswith("//"):
                    continue
                parts = line.rstrip("\n").split("\t")
                kind = parts[1] if len(parts) >= 3 else ""
                head = parts[0].split(",")
                if kind in ("warp", "warp2") and len(parts) >= 4:
                    d = parts[3].split(",")
                    dst = d[2] if len(d) > 2 else d[0]
                    if head[0] != dst:
                        self.edges[head[0]].add(dst)
                        self.walk_edges[head[0]].add(dst)
                        if len(d) >= 5:
                            self.arrivals[dst].append((head[0], int(d[3]), int(d[4])))
                    if len(head) >= 3:
                        self.portals[head[0]].append((int(head[1]), int(head[2])))
                elif kind == "monster" and len(parts) >= 4:
                    a = parts[3].split(",")
                    try:
                        self.spawns[head[0]].append((int(a[0]), int(a[1])))
                    except ValueError:
                        pass
                    if is_dungeon_spawn:
                        self.dungeon_maps.add(head[0])
                elif kind in ("shop", "marketshop") and len(parts) >= 4:
                    for it in parts[3].split(",")[1:]:
                        self.shop_items.add(it.split(":")[0].strip())
                if ("script" in kind or kind in ("shop", "marketshop") or kind.startswith("duplicate")) and len(head) >= 3:
                    try:
                        self.npcs[head[0]].append((int(head[1]), int(head[2])))
                    except ValueError:
                        pass
                if "script" in kind:
                    cur = head[0]
                if cur and 'callfunc "F_Kafra"' in line:
                    kafra.add(cur)
                if cur and script_ok and cur != "-":
                    for dst, x, y in re.findall(r'\bwarp\s*"(\w+)"\s*,\s*(\d+)\s*,\s*(\d+)', line):
                        if dst != cur:
                            self.edges[cur].add(dst)
                            script_edges.append((cur, dst))
                            self.arrivals[dst].append((cur, int(x), int(y)))
        for a, b, x, y in MANUAL_EDGES:
            self.edges[a].add(b)
            self.walk_edges[a].add(b)
        self.hubs = (kafra - NOISE_TOWNS) | KAFRA_EXTRA
        for a, b in script_edges:
            if a in self.hubs:
                self.walk_edges[a].add(b)

    def walking(self):
        """Maps from the nearest town on foot: warps, and the boats and sailors
        in town, but not a quest NPC's shortcut into a dungeon's deep end."""
        return bfs(self.walk_edges, sorted(self.hubs))


def read_yaml_list(path, fields):
    """Read a rAthena YAML DB's Body as dicts. Not a YAML parser: it knows the shape."""
    out, cur, sub = [], None, None
    for line in open(path, errors="ignore"):
        m = re.match(r"  - Id: (\d+)", line)
        if m:
            cur = {"Id": int(m.group(1)), "Drops": []}
            out.append(cur)
            sub = None
            continue
        if cur is None:
            continue
        m = re.match(r"    (\w+):\s*(.*)", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            sub = key
            if key in fields and key not in cur:
                cur[key] = val
            continue
        if sub == "Drops":
            m = re.match(r"\s+- Item: (\S+)", line)
            if m:
                cur["Drops"].append([m.group(1), 0])
            m = re.match(r"\s+Rate: (\d+)", line)
            if m and cur["Drops"]:
                cur["Drops"][-1][1] = int(m.group(1))
    return out


def read_map_cache(rathena, era):
    """Walkability of every map: name -> (width, height, cells), cell 0 = walkable."""
    maps = {}
    for path in (f"{rathena}/db/map_cache.dat", f"{rathena}/db/{era}/map_cache.dat"):
        data = open(path, "rb").read()
        _, count = struct.unpack_from("<IH", data, 0)
        off = 8
        for _ in range(count):
            name = data[off:off + 12].split(b"\0")[0].decode(errors="replace")
            xs, ys, ln = struct.unpack_from("<hhi", data, off + 12)
            off += 20
            maps[name] = (xs, ys, data[off:off + ln])
            off += ln
    return maps


class Cells:
    def __init__(self, entry):
        self.w, self.h, packed = entry
        self.c = zlib.decompress(packed)

    def walkable(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.c[x + y * self.w] == 0

    def open(self, x, y, need=9):
        """Walkable, with enough of the 3x3 around it walkable that the board
        does not plug a corridor. need=9 is fully open."""
        return self.walkable(x, y) and \
            sum(self.walkable(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)) >= need


def bfs(edges, starts):
    dist = {s: 0 for s in starts}
    q = collections.deque(starts)
    while q:
        u = q.popleft()
        for v in edges.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def round50(x):
    return int(round(x / 50.0)) * 50


def suggest_spot(mp, eras, dungeon):
    """A spot for the board beside the warp you walk onto the map by, open in
    every era the map exists in. eras: [(world, cells, nearest)]. Returns
    (x, y, entry map) or None.

    The entry is the warp from the side nearest a town, counted over all eras
    together, so both eras agree on one spot."""
    eras = [e for e in eras if e[1]]
    if not eras:
        return None
    score = collections.defaultdict(int)
    land = {}
    for world, _, nearest in eras:
        for src, x, y in world.arrivals.get(mp, []):
            score[src] += nearest.get(src, 99)
            land.setdefault(src, (x, y))
    for src in score:  # a side missing from an era counts as far away
        score[src] += 99 * sum(1 for w, _, _ in eras if src not in {a[0] for a in w.arrivals.get(mp, [])})
    above = floor_above(mp) if dungeon else None
    if above in score:
        # A dungeon floor: you come down the stairs from the floor above.
        entry = above
        ax, ay = land[entry]
    elif score:
        entry = min(score, key=lambda s: (score[s], s))
        ax, ay = land[entry]
    else:
        entry, (ax, ay) = None, (eras[0][1].w // 2, eras[0][1].h // 2)
    crowd = [p for w, _, _ in eras for p in w.portals.get(mp, []) + w.npcs.get(mp, [])]
    # Fully open spots near the way in first; failing that, a looser spot a
    # little farther out (narrow dungeons such as Magma).
    for need, far in ((9, BOARD_RING[1]), (7, BOARD_RING[1] + 6)):
        for r in range(BOARD_RING[0], far + 1):
            best = None
            for x in range(ax - r, ax + r + 1):
                for y in range(ay - r, ay + r + 1):
                    if max(abs(x - ax), abs(y - ay)) != r:
                        continue
                    if not all(c.open(x, y, need) and land_beside(c, x, y) for _, c, _ in eras):
                        continue
                    if any(max(abs(x - px), abs(y - py)) < BOARD_KEEP_CLEAR for px, py in crowd):
                        continue
                    # The spot closest to straight ahead of the warp.
                    key = abs(x - ax) + abs(y - ay)
                    if best is None or key < best[0]:
                        best = (key, x, y)
            if best:
                return best[1], best[2], entry
    return None


def floor_above(mp):
    """The floor above a numbered dungeon floor, by name: pay_dun02 ->
    pay_dun01, gl_prison1 -> gl_prison. None for an unnumbered map."""
    m = re.match(r"(.*?)(\d+)$", mp)
    if not m:
        return None
    n = int(m.group(2)) - 1
    if n < 0:
        return None
    if n == 0 and len(m.group(2)) == 1:
        return m.group(1)
    return m.group(1) + str(n).zfill(len(m.group(2)))


def land_beside(cells, bx, by):
    """Where a warp to the board puts the traveller: two cells south of it, or
    anywhere beside it."""
    for dx, dy in ((0, -2), (0, -1), (1, -1), (-1, -1), (2, 0), (-2, 0), (0, 2), (1, 1), (-1, 1)):
        if cells.walkable(bx + dx, by + dy):
            return bx + dx, by + dy
    return None


def build(rathena, era, rows):
    world = World(rathena, era)
    cache = read_map_cache(rathena, era)
    mobs = {m["Id"]: m for m in read_yaml_list(f"{rathena}/db/{era}/mob_db.yml",
                                                {"Name", "Level", "Class", "Ai", "MvpExp"})}
    items = {}
    for p in glob.glob(f"{rathena}/db/{era}/item_db*.yml"):
        for it in read_yaml_list(p, {"AegisName", "Name", "Type"}):
            items[it.get("AegisName")] = it
    sold = {a for a, it in items.items() if a in world.shop_items or str(it["Id"]) in world.shop_items}

    # Floor depth: how many dungeon maps deep, walking in from outside.
    dun = world.dungeon_maps
    outside = [m for m in set(world.edges) | {d for v in world.edges.values() for d in v} if m not in dun]
    depth = {m: d for m, d in bfs({u: {v for v in vs if v in dun} for u, vs in world.edges.items()},
                                  outside).items() if m in dun}
    nearest = bfs(world.edges, sorted(world.hubs))

    out = []
    for r in rows:
        mp, typ = r["Map"], r["Type"]
        w = dict(r, Era=era)
        out.append(w)
        if mp not in cache:
            w["Skip"] = "map not in this era"
            continue
        pop = [(mobs[i], n) for i, n in world.spawns.get(mp, []) if i in mobs]
        eligible = [(m, n) for m, n in pop if m.get("Ai") not in PLANT_AI and "MvpExp" not in m]
        total = sum(n for _, n in eligible)
        if not total:
            w["Skip"] = "no eligible spawns"
            continue
        level = round(sum(int(m.get("Level", 1)) * n for m, n in eligible) / total)
        high = level >= HIGH_BAND[era]
        budget = BUDGET[(typ, high)]

        # Expected drops per kill of each Etc item, and which mob gives the most.
        share = collections.Counter()
        for m, n in eligible:
            share[m.get("Name")] += n / total
        epk, source, best_rate = collections.Counter(), {}, {}
        for m, n in eligible:
            for aegis, rate in m["Drops"]:
                it = items.get(aegis)
                if not it or it.get("Type") != "Etc" or aegis in EXCLUDE_ITEMS or aegis in sold:
                    continue
                gain = n / total * min(rate * SERVER_DROP_RATE, 10000) / 10000
                epk[aegis] += gain
                if gain > source.get(aegis, (None, 0, 0))[1]:
                    source[aegis] = (m.get("Name"), gain, rate)
                if share[m.get("Name")] >= UNCOMMON_MIN_SHARE:
                    best_rate[aegis] = max(best_rate.get(aegis, 0), rate)

        picks, used_mobs = [], set()

        def pick(cands, n, lo_hi):
            for a in cands:
                if len(picks) >= n:
                    return
                if a in (p[0] for p in picks):
                    continue
                if source[a][0] in used_mobs and len(cands) > n:
                    continue
                picks.append((a, min(lo_hi[1], max(lo_hi[0], round(budget * epk[a])))))
                used_mobs.add(source[a][0])

        ranked = [a for a, _ in epk.most_common()]
        commons = [a for a in ranked if epk[a] >= COMMON_MIN] or \
                  [a for a in ranked if source[a][2] >= UNCOMMON[0]][:1]
        uncommons = [a for a in ranked if UNCOMMON[0] <= best_rate.get(a, 0) <= UNCOMMON[1]]
        pick(commons, 2 if high else 1, QTY_COMMON)
        if typ == "Dungeon":
            pick(uncommons, len(picks) + 1, QTY_UNCOMMON)
        if not picks:
            w["Skip"] = "no item qualifies: pick one by hand"
            continue

        hops = nearest.get(mp)
        if hops is None:
            w["Skip"] = "no route from any town"
            continue
        floors = max(0, depth.get(mp, 1) - 1) if typ == "Dungeon" else 0
        fee = min(FEE_CAP, round50(max(FEE_BASE + FEE_PER_HOP * hops, FEE_PER_LEVEL[typ] * level)
                                   + FEE_PER_FLOOR * floors))
        if not (r.get("BoardX") and r.get("BoardY")):
            w["Skip"] = "no BoardX,BoardY: run --fill-spots"
            continue
        board = (int(r["BoardX"]), int(r["BoardY"]))
        cells = Cells(cache[mp])
        landing = land_beside(cells, *board) if cells.walkable(*board) else None
        if not landing:
            w["Skip"] = f"BoardX,BoardY {board[0]},{board[1]} is not walkable here"
            continue
        w.update(Level=level, High=high, Budget=budget, Floor=depth.get(mp), Hops=hops, Fee=fee,
                 Board=board, Land=landing,
                 Items=[(items[a]["Id"], items[a]["Name"], q, source[a][0], source[a][2]) for a, q in picks])
    return world, cache, out


def read_csv(name):
    with open(os.path.join(HERE, name), newline="") as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))


def check_towns(towns, cache, world, era):
    ok = []
    for t in towns:
        if t["Era"] not in ("any", era):
            continue
        if t["Map"] not in cache:
            print(f"  town {t['Map']}: not a map in {era}, left out", file=sys.stderr)
            continue
        x, y = int(t["X"]), int(t["Y"])
        if not Cells(cache[t["Map"]]).walkable(x, y):
            print(f"  town {t['Map']}: {x},{y} is not walkable in {era}, left out", file=sys.stderr)
            continue
        ok.append(t)
    return ok


def script_text(era, waypoints, towns):
    q = lambda s: '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    live = [w for w in waypoints if "Skip" not in w]
    L = ["//===== Ragnarok Offline: waypoint-system ===================",
         f"//= Generated for {'renewal' if era == 're' else 'pre-renewal'} by",
         "//= registry/tools/waypoint-system/build_waypoints.py --write.",
         "//= Do not edit: change waypoints.csv or towns.csv and regenerate.",
         "//============================================================",
         "",
         "// What each waypoint is, indexed by its permanent Id.",
         "-\tscript\tWaypointData\t-1,{",
         "OnInit:"]
    ids = [int(w["Id"]) for w in live]
    L.append(f"\t$@WP_MAXID = {max(ids) if ids else 0};")
    L.append(f"\tsetarray $@WP_IDS[0], {', '.join(map(str, ids))};")
    for w in live:
        i = int(w["Id"])
        sets = [f'$@WP_MAP$[{i}] = {q(w["Map"])};',
                f'$@WP_NAME$[{i}] = {q(w["Region"] + " - " + w["Name"])};',
                f'$@WP_TYPE[{i}] = {0 if w["Type"] == "Field" else 1};',
                f'$@WP_FEE[{i}] = {w["Fee"]};',
                f'$@WP_X[{i}] = {w["Land"][0]}; $@WP_Y[{i}] = {w["Land"][1]};']
        for n, (iid, _, qty, _, _) in enumerate(w["Items"], 1):
            sets.append(f"$@WP_IT{n}[{i}] = {iid}; $@WP_QT{n}[{i}] = {qty};")
        names = "; ".join(f"{qty}x {nm}" for _, nm, qty, _, _ in w["Items"])
        L.append(f"\t// {w['Map']}: L{w['Level']}, {w['Hops']} maps from town, {names}")
        L.extend("\t" + s for s in sets)
    for t in towns:
        L.append(f'\t$@WPT_{t["Map"]}$ = {q(t["Name"])};')
    L += ["\tend;", "}", "", "// The boards, one per waypoint."]
    for w in live:
        bx, by = w["Board"]
        L.append(f"{w['Map']},{bx},{by},4\tduplicate(WaypointBoard)\tWaypoint#{w['Id']}\t858")
    L += ["", "// The Waypoint Keepers, one per town."]
    # rAthena caps an NPC's full name, # part included, at 24 characters.
    for n, t in enumerate(towns, 1):
        L.append(f"{t['Map']},{t['X']},{t['Y']},{t['Dir']}\tduplicate(WaypointKeeper)\tWaypoint Keeper#{n}\t19510")
    return "\n".join(L) + "\n"


def fill_spots(rathena):
    """Write a suggested BoardX,BoardY into every row of waypoints.csv that has
    none. Rows that already have a spot are left exactly as they are."""
    path = os.path.join(HERE, "waypoints.csv")
    lines = open(path, newline="").read().splitlines()
    comments = [l for l in lines if l.startswith("#")]
    rows = list(csv.DictReader(l for l in lines if not l.startswith("#")))
    if not any(not (r["BoardX"] and r["BoardY"]) for r in rows):
        print("every waypoint already has a spot")
        return
    eras = []
    for era in ("re", "pre-re"):
        world = World(rathena, era)
        eras.append((world, read_map_cache(rathena, era), world.walking()))
    for r in rows:
        if r["BoardX"] and r["BoardY"]:
            continue
        spot = suggest_spot(r["Map"], [(w, Cells(c[r["Map"]]) if r["Map"] in c else None, n) for w, c, n in eras],
                            r["Type"] == "Dungeon")
        if not spot:
            print(f"{r['Id']:>3} {r['Map']:12} no open spot found: set BoardX,BoardY by hand")
            continue
        r["BoardX"], r["BoardY"] = str(spot[0]), str(spot[1])
        print(f"{r['Id']:>3} {r['Map']:12} {spot[0]},{spot[1]}  beside the warp from {spot[2]}")
    with open(path, "w", newline="") as f:
        f.write("\n".join(comments) + "\n")
        out = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        out.writeheader()
        out.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rathena", default=os.environ.get("RATHENA_DIR", os.path.join(ROOT, "vendor/rathena")))
    ap.add_argument("--era", choices=["re", "pre-re"], action="append")
    ap.add_argument("--preview", help="also write the table to this CSV, for review")
    ap.add_argument("--write", action="store_true", help="write the mod's generated scripts")
    ap.add_argument("--fill-spots", action="store_true",
                    help="put a suggested BoardX,BoardY into every waypoints.csv row that has none")
    a = ap.parse_args()
    if a.fill_spots:
        fill_spots(a.rathena)
    rows, towns = read_csv("waypoints.csv"), read_csv("towns.csv")
    preview = []
    for era in a.era or ["pre-re", "re"]:
        print(f"===== {era}")
        world, cache, built = build(a.rathena, era, rows)
        for w in built:
            if "Skip" in w:
                print(f"{w['Id']:>3} {w['Map']:12} {w['Type']:7} SKIP {w['Skip']}")
                continue
            it = "; ".join(f"{q}x {n} [{s} {r / 100:g}%]" for _, n, q, s, r in w["Items"])
            print(f"{w['Id']:>3} {w['Map']:12} {w['Type']:7} L{w['Level']:<3}{'H' if w['High'] else ' '} "
                  f"floor{w['Floor'] or '-'} hops {w['Hops']} fee {w['Fee']:<5} board {w['Board'][0]},{w['Board'][1]}"
                  f"  kills~{w['Budget']}  {it}")
            preview.append([era, w["Id"], w["Map"], w["Type"], w["Name"], w["Level"], "H" if w["High"] else "",
                            w["Hops"], w["Fee"], w["Budget"]] + [f"{q}x {n} ({s} {r / 100:g}%)" for _, n, q, s, r in w["Items"]])
        live_towns = check_towns(towns, cache, world, era)
        if a.write:
            path = os.path.join(MOD, OUT[era])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", newline="\n") as f:
                f.write(script_text(era, built, live_towns))
            print(f"wrote {os.path.relpath(path, ROOT)}")
    if a.preview:
        with open(a.preview, "w", newline="") as f:
            out = csv.writer(f, lineterminator="\n")
            out.writerow(["Era", "Id", "Map", "Type", "Name", "Level", "Band", "Hops", "Fee", "Kills", "Item1", "Item2", "Item3"])
            out.writerows(preview)


if __name__ == "__main__":
    sys.exit(main())
