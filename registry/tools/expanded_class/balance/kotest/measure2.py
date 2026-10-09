#!/usr/bin/env python3
"""measure2.py user pass job weapon ammo skills levels [secs] [how=mob|self|pos] [pre-skill:lv,...]
Template character (build#), equips weapon+ammo, dummy beside it, spams the skills, prints DPS.
pre: skills cast once before the loop and every 10 s (markers, buffs)."""
import json, os, subprocess, sys
a = sys.argv[1:]
user, pw, job, weapon, ammo, sids, lvs = a[:7]
secs = float(a[7]) if len(a) > 7 else 30
how = a[8] if len(a) > 8 else "mob"
pre = [x.split(":") for x in a[9].split(",")] if len(a) > 9 and a[9] not in ("", "-") else []   # id:lv[:self]
sids = sids.split(","); lvs = lvs.split(",")
selfs = {x.rstrip("s") for x in sids if x.endswith("s")}   # "2592s": cast on yourself
sids = [x.rstrip("s") for x in sids]
head = [f"whisper npc:KoTest build#{job}#{weapon}", "wait 3", "whisper npc:KoTest rlkit"]
if ammo != "0": head += [f"whisper npc:KoTest gun#{weapon}#{ammo}", "wait 1"]
if os.environ.get("LEFT"):   # LEFT=<item id>: a second weapon in the left hand (dual wielding)
    head += [f"whisper npc:KoTest give#{os.environ['LEFT']}", "wait 2", "wear-given 0x20", "wait 1"]
import os
MOBT = "mob:25503" if os.environ.get("DUMMY") == "dummy#4" else "mob:25500"   # the target
head += [c for c in os.environ.get("EXTRA", "").split(";") if c]   # EXTRA="whisper npc:KoTest mount#2;wait 1"
head += ["whisper npc:KoTest " + os.environ.get("DUMMY", "dummy"), "wait 2", "mobs"]   # DUMMY=dummy#2: other side
hpcheck = os.environ.get("HPCHECK") == "1"   # also read the dummy's HP before and after: hp_dps, what it really lost
if hpcheck: head += ["whisper npc:KoTest mobhp#0", "wait 1"]
p = subprocess.Popen(["python3", "roclient.py", "--user", user, "--pass", pw, "run", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
for l in head: p.stdin.write(l + "\n")
p.stdin.flush()
pos = None; buf = []
while pos is None:
    l = p.stdout.readline()
    if not l: break
    buf.append(l)
    try: e = json.loads(l)
    except Exception: continue
    if e.get("ev") == "mob" and e.get("class") in (25500, 25503): pos = f"{e['x']} {e['y']}"
step = float(a[10]) if len(a) > 10 else 0.1; body = []   # STEP: pace long casts
paced = len(a) > 11 and a[11] == "paced"   # one cast at a time: the next only once the last has landed
noheal = os.environ.get("NOHEAL") == "1"   # SP is not refilled: read before and after
if paced:
    pairs = list(zip(sids, lvs))
    if noheal:
        body += ["whisper npc:KoTest heal", "wait 2", "whisper npc:KoTest sp#-1", "wait 2"]
    body.append(f"deadline {secs}")
    for p_ in pre:
        body.append(f"cast {p_[0]} {p_[1]} {'self' if 'self' in p_ else MOBT}")
    for i in range(int(secs / 0.3)):
        if i % 6 == 0 and not noheal: body.append("whisper npc:KoTest heal")
        for s, l in pairs:
            h = "self" if s in selfs else how
            body.append({"mob": f"cast {s} {l} {MOBT}", "self": f"cast {s} {l} self", "pos": f"cast-pos {s} {l} {pos}"}[h])
for i in range(0 if paced else int(secs / step)):
    if i % max(1, int(3 / step)) == 0: body.append("whisper npc:KoTest heal")
    if i % max(1, int(10 / step)) == 0:
        if "attack" in sids and pre:
            body.append("stop-attack")          # a cast bar is not interrupted by attacking
        for p_ in pre:
            if "once" in p_ and i > 0:          # toggles and long buffs: cast at the start only
                continue
            body += [f"skill {p_[0]} {p_[1]} {'self' if 'self' in p_ else MOBT}",
                     "dump-damage 2.6" if "attack" in sids else "dump-damage 0.6"]
    seq = len(a) > 11 and a[11] == "seq"      # one skill per tick, in turn
    pairs = list(zip(sids, lvs))
    for s, l in ([pairs[i % len(pairs)]] if seq else pairs):
        if s == "attack":
            body.append("attack " + MOBT); continue
        h = "self" if s in selfs else how
        body.append({"mob": f"skill {s} {l} {MOBT}", "self": f"skill {s} {l} self", "pos": f"skill-pos {s} {l} {pos}"}[h])
    body.append(f"dump-damage {step}")
body.append("dump-damage 2")
if hpcheck: body += ["whisper npc:KoTest mobhp#0", "wait 1"]
if paced and noheal:
    body += ["whisper npc:KoTest sp#-1", "wait 3"]
if os.environ.get("DUMPBODY"): open(os.environ["DUMPBODY"], "w").write("\n".join(body) + "\n")
for l in body: p.stdin.write(l + "\n")
p.stdin.write("quit\n"); p.stdin.close()
out = "".join(buf) + p.stdout.read()
aid = None; total = 0; casts = 0; other = {}; fails = {}; per = {}; per_n = {}
sps = [int(x) for x in __import__("re").findall(r"KoTest: sp (\d+)/", out)]
evs = []
for l in out.splitlines():
    try: evs.append(json.loads(l))
    except Exception: pass
aid = next((e["aid"] for e in evs if e.get("ev") == "map_entered"), None)
# some ground skills (Fire Rain) report each hit twice, from the unit and from the caster
mine = {}
for e in evs:
    if e.get("ev") == "skill_damage" and e.get("src") == aid:
        mine.setdefault((e.get("skill"), e.get("target"), e.get("damage")), []).append(e.get("t", 0))
def echoed(e):
    return e.get("src") != aid and any(abs(t - e.get("t", 0)) < 0.05 for t in mine.get((e.get("skill"), e.get("target"), e.get("damage")), []))
for e in evs:
    # ground skills report from their skill unit, not the caster: count by skill id
    if e.get("ev") in ("skill_damage", "damage") and e.get("target") != aid and (e.get("src") == aid or str(e.get("skill", 0)) in sids) and not echoed(e):
        k = str(e.get("skill", 0))
        if k == "0" and "attack" in sids: k = "attack"
        if k in sids:
            total += max(0, e.get("damage", 0)); casts += 1
            per[k] = per.get(k, 0) + max(0, e.get("damage", 0)); per_n[k] = per_n.get(k, 0) + 1
        else: other[k] = other.get(k, 0) + max(0, e.get("damage", 0))
    if e.get("ev") == "skill_fail" and str(e.get("skill")) in sids:
        fails[e.get("cause")] = fails.get(e.get("cause"), 0) + 1
hps = [int(x) for x in __import__("re").findall(r"KoTest: mobhp (\d+) /", out)]
print(json.dumps({"hp_dps": round((hps[0] - hps[-1]) / secs) if len(hps) >= 2 else None, "job": job, "skill": ",".join(sids), "lv": ",".join(lvs), "dps": round(total / secs), "casts": casts,
                  "per_cast": round(total / casts) if casts else 0, "other_dps": {k: round(v / secs) for k, v in other.items()}, "fails": fails, "per_skill": {k: [round(v / secs), per_n[k]] for k, v in per.items()}, "sp_net_per_s": round((sps[0] - sps[-1]) / secs, 1) if len(sps) >= 2 else None, "sp_start": sps[0] if sps else None}))
