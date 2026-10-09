# Balance rig for the class mods

A pre-renewal rAthena server and a headless client that plays it, used to
measure the class mods' skills (damage per second on a test dummy) and to
check them against the aims in each mod's `balance.json`. Nothing here ships
with the app. `docs/mods/EXPANDED_CLASS_REBIRTH.md` (§7, §12) explains how
the numbers are used.

## Use

Needs docker. Once:

```
registry/tools/expanded_class/balance/setup.sh ../rathena   # or vendor/rathena (the default)
```

clones the rAthena commit `config/VENDOR_PINS` pins into `./rathena` (not
committed) and builds it for pre-renewal, packet version 20221005. Run it
again after the pin moves.

Then, for a mod with a spec (generate the mod first with its `build.py`):

```
python3 registry/tools/expanded_class/balance/run_specs.py registry/tools/transcendent-third-classes/balance.json
python3 registry/tools/expanded_class/balance/run_specs.py <spec> --only RK_SonicWave
```

It starts the servers with the spec's mods loaded, measures each run, and
prints its damage per second, the ratio to the run it is compared with and
whether that ratio is inside the aim. It exits 1 when one is not. A full
spec takes one to two hours; the server runs in the background meanwhile.
`./down.sh` stops it (`--wipe` also deletes its database).

The spec format is described at the top of `run_specs.py`.

## Pieces

| | |
|---|---|
| `setup.sh`, `build.sh` | clone and build rAthena in `docker/Dockerfile`'s toolchain image |
| `up.sh`, `down.sh` | start/stop a MariaDB container (`rorig-db`, port 13306) and the servers (`rorig-server`), with mod directories installed into the import layer |
| `base/` | the servers' config and the test accounts (`player`, `axe`, `fem`, `gmtest`; passwords `<name>123`) |
| `roclient.py` | the headless client: logs in and runs commands (`skill`, `cast`, `attack`, `use`, `wear`, `talk`, `menu`, `whisper`, ...); `pktlen.json` is its packet table (`tools/gen_pktlen.sh` regenerates it) |
| `kotest/` | the test helper (an NPC driven by whispers), test weapons 59001-59016 and dummies 25500 and 25503, and the measuring scripts |
| `spelltest/` | monsters that cast spells at you, for copied-skill tests (load it as a mod) |

`kotest/npc/kotest.txt` lists the helper's commands, for example
`build#<job>#<weapon>` (the measuring template), `dummy#4` (the anchored
dummy), `mount#2` (a dragon), `mobhp#0` (the dummy's HP), `sp#-1` (your SP),
`give#<item>`, `rune#<skill>`, `learn#<skill>`.

## Things that mislead

- A new skill request restarts a cast in progress, a dummy that hits back
  interrupts casts, and a dummy that cannot be knocked back takes every hit
  of a knockback skill that a real monster would escape. Use `method` and
  `dummy` in the spec accordingly (paced for cast-time skills, the normal
  dummy for knockback skills).
- `dump-damage` prints only what arrives while it streams. Before calling a
  skill broken, read the dummy's HP (`mobhp#0`).
- One measurement at a time: the helper's `dummy` command kills every
  monster on the map, so two runs on one server spoil each other.
- `rlkit` gives the Rebellion's consumables; giving them twice overloads the
  character, which then cannot use skills.
