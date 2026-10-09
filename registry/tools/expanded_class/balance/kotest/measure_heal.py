#!/usr/bin/env python3
"""measure_heal.py user pass job weapon skill lv casts gap [self|pos]
Template caster (build#), SP to max; per cast: HP to 1, cast on yourself,
wait GAP, read HP and SP. Prints heal per cast and SP per cast.
measure_heal.py user pass job weapon regen secs: SP to 0, stand SECS, SP gained."""
import json, re, subprocess, sys
a = sys.argv[1:]
user, pw, job, weapon = a[:4]
cmds = [f"whisper npc:KoTest build#{job}#{weapon}", "wait 3", "whisper npc:KoTest rlkit", "wait 1"]
if a[4] == "regen":
    cmds += ["whisper npc:KoTest sp#0", "wait 1", f"wait {a[5]}", "whisper npc:KoTest sp#-1", "wait 1"]
else:
    sid, lv, n, gap = a[4], a[5], int(a[6]), float(a[7])
    how = a[8] if len(a) > 8 else "self"
    cmds += ["whisper npc:KoTest sp#99999", "wait 1"]
    for _ in range(n):
        cmds += ["whisper npc:KoTest sp#-1", "whisper npc:KoTest hp#1", "wait 0.3",
                 f"skill {sid} {lv} self" if how == "self" else f"skill-pos {sid} {lv} 150 150", f"wait {gap}"]
    cmds += ["whisper npc:KoTest sp#-1", "wait 1"]
out = subprocess.run(["python3", "roclient.py", "--user", user, "--pass", pw, "run", "-"], input="\n".join(cmds) + "\nquit\n",
                     capture_output=True, text=True).stdout
rows = [tuple(map(int, m)) for m in re.findall(r"KoTest: sp (\d+)/(\d+) hp (\d+)/(\d+)", out)]
if a[4] == "regen":
    print(json.dumps({"job": job, "regen_secs": float(a[5]), "sp_gained": rows[-1][0], "max_sp": rows[-1][1]}))
else:
    heals = [r[2] - 1 for r in rows[1:]]           # HP after each cast (HP was 1 before it)
    sp = [rows[i][0] - rows[i + 1][0] for i in range(len(rows) - 1)]
    landed = [i for i, s in enumerate(sp) if s > 0]
    print(json.dumps({"job": job, "skill": sid, "lv": lv, "landed": f"{len(landed)}/{n}",
                      "heal_per_cast": round(sum(heals[i] for i in landed) / len(landed)) if landed else 0,
                      "sp_per_cast": round(sum(sp[i] for i in landed) / len(landed)) if landed else 0,
                      "max_hp": rows[0][3], "max_sp": rows[0][1]}))
