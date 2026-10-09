#!/usr/bin/env python3
"""Measure a class mod's balance from its spec file and compare it with the aims.

    python3 registry/tools/expanded_class/balance/run_specs.py registry/tools/<mod>/balance.json
    ... --only GX_CI,AX_SB      measure only these runs (and what they are compared with)
    ... --no-load               use the mods the test server already has loaded

A spec file lists runs. Each run is one rotation on the measuring template
(kotest's build#: base 99, job 70, a STR/AGI, DEX or INT/DEX build by class)
against a test dummy for SECONDS, and its result is damage per second on that
one target (for an area skill: on each target). A run may name another run as
`versus` and an `aim`, a band for the ratio of the two.

Run fields (only id, class, weapon, skills and levels are required):
    id        a name for the run
    class     the job id (4013 Assassin Cross, 4065 Guillotine Cross T, ...)
    weapon    item id, usually a test weapon from kotest/db/item_db.yml
    ammo      ammunition item id (arrows, bullets), 0 for none
    left      item id of a second weapon worn in the left hand (dual wielding)
    stats     "int", "dex" or "str": that stat build instead of the class's usual one
    user      the test account to play (default "player"; "fem" for female-only classes)
    skills    comma-separated skill ids cast in turn; "attack" for auto-attacks;
              a trailing "s" casts on yourself (2036s)
    levels    their levels, comma-separated
    how       "mob" (cast on the dummy) or "pos" (on the dummy's cell)
    pre       "id:lv[:self][:once]" casts before the rotation and every 10 s
    extra     kotest commands before the dummy, ";"-separated (a shield, a dragon)
    charge    "id:lv:n": cast a self skill n times before the dummy (charms:
              "3016:1:10" holds ten water charms through the run)
    dummy     "anchored" (default: never hits back, cannot be knocked back),
              "normal" (hits back; use it for skills that knock targets away) or
              "mdef" (anchored, with high magic defence: MDEF 40, INT 80, VIT 50)
    method    "step" (requests at a fixed pace: instant skills), "paced" (one
              cast at a time: cast-time skills) or "best" (both, the higher)
    step      seconds between requests for "step" (default 0.1), or a list of
              them to try, the highest kept (casters' rhythms differ: [1.0, 1.5])
    seq       true: one skill per step, in turn
    repeat    measurements per method, the highest kept (default 2)
    versus    the id of the run this one is compared with
    aim       [low, high] for this run's result / versus's result

The rig must be set up (setup.sh) and the mod generated (its build.py).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def measure(run, seconds):
    method = run.get("method", "step")
    steps = run.get("step", 0.1)
    steps = steps if isinstance(steps, list) else [steps]
    modes = ([("step", s) for s in steps] if method != "paced" else []) + ([("paced", 1)] if method != "step" else [])
    results = []
    for mode, step in modes:
        if mode == "paced":
            tail = ["1", "paced"]
        else:
            tail = [str(step)] + (["seq"] if run.get("seq") else [])
        user = run.get("user", "player")
        args = ["python3", "kotest/measure2.py", user, user + "123", str(run["class"]), str(run["weapon"]),
                str(run.get("ammo", 0)), str(run["skills"]), str(run["levels"]), str(seconds),
                run.get("how", "mob"), run.get("pre") or "-"] + tail
        extra = run.get("extra", "")
        if run.get("charge"):
            sid, lv, n = run["charge"].split(":")
            extra = ";".join([f"skill {sid} {lv} self;wait 0.8"] * int(n) + ([extra] if extra else []))
        env = {**os.environ, "EXTRA": extra, "LEFT": str(run.get("left", "")), "STATS": run.get("stats", ""),
               "DUMMY": {"anchored": "dummy#4", "mdef": "dummy#5"}.get(run.get("dummy", "anchored"), "dummy")}
        for _ in range(int(run.get("repeat", 2))):
            try:
                out = subprocess.run(args, cwd=HERE, env=env, capture_output=True, text=True,
                                     timeout=seconds * 3 + 120).stdout
            except subprocess.TimeoutExpired:
                continue
            for line in out.splitlines():
                if line.startswith("{"):
                    d = json.loads(line)
                    results.append(d["dps"] + sum(d["other_dps"].values()))
    return max(results) if results else 0, results


def main():
    ap = argparse.ArgumentParser(description="Measure a class mod's balance from its spec file.")
    ap.add_argument("spec", type=Path)
    ap.add_argument("--only", default="", help="comma-separated run ids")
    ap.add_argument("--no-load", action="store_true", help="do not (re)start the server with the spec's mods")
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text())
    runs = {r["id"]: r for r in spec["runs"]}
    wanted = [i for i in args.only.split(",") if i] or list(runs)
    for i in list(wanted):
        v = runs[i].get("versus")
        if v and v not in wanted:
            wanted.insert(0, v)
    if not args.no_load:
        mods = [str(ROOT / m) for m in spec.get("load", [])] + [str(HERE / "kotest")]
        out = subprocess.run([str(HERE / "up.sh")] + mods, capture_output=True, text=True)
        status = [l for l in out.stdout.splitlines() if l.startswith("map.log")]
        print(status[0] if status else out.stdout[-400:], flush=True)
    seconds = int(spec.get("seconds", 40))
    value, outside = {}, 0
    print(f"{'run':28} {'dmg/s':>7}  {'ratio':>6}  aim         all measurements", flush=True)
    for i in (r for r in runs if r in wanted):
        run = runs[i]
        value[i], allv = measure(run, seconds)
        ratio, verdict = "", ""
        if run.get("versus") in value and value[run["versus"]]:
            r = value[i] / value[run["versus"]]
            ratio = f"{r:.2f}"
            if "aim" in run:
                lo, hi = run["aim"]
                ok = lo <= r <= hi
                outside += not ok
                verdict = f"{lo:.2f}-{hi:.2f} {'ok' if ok else 'OUT'}"
        print(f"{i:28} {value[i]:7}  {ratio:>6}  {verdict:11} {allv}", flush=True)
    sys.exit(1 if outside else 0)


if __name__ == "__main__":
    main()
