# shell-gz

When you level up, one to three of the AI characters near you stop for a
moment and say "gz", or throw a congratulations emote. It is the smallest
useful thing the shell control commands do, and the place to start reading.

**Needs an app with the shell control commands** (population engine patch
0027). On an older one the server rejects both scripts at load, with an
"unknown command" line in the map server log.

Compiled, not yet run in game.

## What to look at first

`npc/shell_gz.txt`. Four lines carry it:

- `population_shells` lists the shells around you, nearest first. Without
  flags it lists only ones a script may take: ambient, alive, not held.
- `population_hold` takes one from the engine for five seconds, so it stops
  walking while it "types".
- `unittalk` and `emotion` are stock rAthena; a shell is a real character.
- `population_unhold` hands it back. If the player logs out halfway, the
  script stops and the hold lapses by itself.

The full reference is [docs/mods/shell-control.md](../../../docs/mods/shell-control.md).

## The test bench

`npc/shell_test.txt` is for GMs (group level 60 and up). Whisper to
`npc:shelltest`, separating arguments with `#`:

| whisper | does |
|---|---|
| `near` | lists the shells within 14 cells with their kind |
| `spawn#Priest#50#Name` | makes a shell beside you and takes it (level and name optional) |
| `grab` | takes the nearest free shell |
| `come` | it walks to you (`unitwalk`) |
| `follow` / `stop` | it follows you, or stops (`pcfollow`) |
| `attack` | it attacks a monster within 14 cells of you, walking into range first (`unitattack`) |
| `warp` / `warp#prt_fild08#150#200` | it warps beside you, or to that spot (`unitwarp`) |
| `say#hello` | it talks (`unittalk`) |
| `free` | gives it back (`population_unhold`) |
| `bye` / `bye#fly` | it logs out, or fly-wings away (`population_despawn`) |

The bench holds one shell at a time. Taking another with `spawn` or `grab`
releases the one before: a spawned shell logs out, a grabbed one goes back to
the AI.

While you hold it, whisper the shell itself: the bench answers through
`population_whisperevent` and `population_whisper`.

`follow`, `attack` and `warp` are stock commands written for players. A
player's client does part of their work (walking into range, finishing a
warp), and a shell has no client, so the engine does that part for a shell
you hold. `follow` carries on through warps the same way.
