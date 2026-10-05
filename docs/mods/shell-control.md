# Directing the AI characters from a script

The AI characters ("shells") run themselves: they fight, wander, sit and chat
by the population engine's rules. A mod that wants one to do something
particular — say "gz" when you level, hold a conversation, wall off a warp,
drag a mob train to you — takes it away from the engine for a while and
drives it from an NPC script.

[Making mods](../MODDING.md) is the general guide. This page is the reference
for the eight `population_*` commands that make the hand-over possible. The
[shell-gz example](../../examples/mods/shell-gz) uses them, and its
`npc:shelltest` NPC lets a GM try each one in game.

## A shell is a real character

That is the whole trick. A shell is a `map_session_data` on the map like any
player, so the stock commands that take a unit id already work on it:

| to make it | use |
|---|---|
| walk to a cell | `unitwalk <gid>, <x>, <y>{, "<npc>::<label>"}` — the label runs when it arrives |
| walk to someone | `unitwalkto <gid>, <target gid>` |
| follow someone | `pcfollow <gid>, <target gid>` / `pcstopfollow <gid>` — through warps too |
| attack | `unitattack <gid>, <target gid>, 1` — 1 keeps attacking; it walks into range first |
| cast | `unitskilluseid <gid>, "<skill>", <level>{, <target gid>}` / `unitskillusepos` |
| say something | `unittalk <gid>, rid2name(<gid>) + " : text"` |
| emote | `emotion <emotion>, <gid>` |
| sit or stand | `sit rid2name(<gid>)` / `stand rid2name(<gid>)` |
| warp | `unitwarp <gid>, "<map>", <x>, <y>` |
| tell its level, job | `readparam(BaseLevel, rid2name(<gid>))`, `readparam(Class, rid2name(<gid>))` — by name: a number there is a character id, not a unit id |

`unittalk` shows its text exactly as given. Real chat reads `Name : text`, so
put the name in front yourself, as above.

Three of these lean on the player's game client for part of their work, and a
shell has none, so **the engine does that part for a shell you hold**:

- `unitattack` only swings at a target already in reach; for anything further
  the server asks the client to walk over. A held shell is walked into range
  instead, and keeps chasing a target that moves.
- `unitwarp`, and `pcfollow` when its target leaves through a warp, move the
  character and wait for the client to say the new map has loaded. A held
  shell's warp is finished within a tenth of a second instead. On a shell
  nobody holds, they leave it off the map and the engine clears it away.

**But the engine is driving it too.** Without a hold, the shell's own AI
overrides your `unitwalk` on its next tick. That is what the commands below
are for.

## The commands

Flags and kinds are plain numbers; there are no named constants for them.

### `population_isshell(<gid>)`

`0` not a shell (a real player, or nothing), `1` ambient, `2` vendor (a
vending stall or buying store), `3` companion (recruited into a player's
party, or with an invitation pending). Event labels such as
`OnPCBaseLvUpEvent` fire for companions too; this is how to skip them.

### `population_shells("<map>", <x>, <y>, <range>, <array>{, <flags>})`

Fills `<array>` with the unit ids of the shells within `<range>` cells of
(x, y), **nearest first**, and returns how many it found, or `-1` for an
unknown map. `<range>` below 0 searches the whole map. Like `getunits`, it
does not clear what the array held past that count, so loop to the returned
number.

With no flags you get only shells you could take: live, ambient, and not held
by any script. Flags add more:

| flag | adds |
|---|---|
| `1` | vendors |
| `2` | shells a script holds, your own included |
| `4` | the dead |

Companions are never listed.

### `population_hold(<gid>{, <milliseconds>})`

Takes the shell away from the engine for that long: default 60000, at least
1000, at most 1800000 (30 minutes). It stops what it was doing, and until the
hold ends the engine does not:

- fight, or fight back when hit
- wander
- say ambient chat lines, or reply to someone mentioning its name
- answer whispers (see `population_whisperevent`)
- warp it back to its own map

Calling it again from the same NPC extends the hold. Returns 1 when held, and
0 for a companion, a vendor, a shell being removed, or one **another NPC**
holds. Holds belong to the NPC that took them, so two mods never fight over
one actor.

A held shell is still a character: monsters can hit it and it can die. A
shell that dies respawns where the engine put it, as usual.

### `population_unhold(<gid>)`

Hands the shell back. Only the NPC that holds it may. Its AI picks up where
the engine sees fit, standing it up first if your script sat it down.

Two cases log out instead of going back:

- a shell `population_spawn` made, unless it was spawned to stay;
- a shell your script left on a map other than its own, which the engine
  would otherwise warp home in plain view.

**A hold also ends by itself** when it lapses or when its NPC no longer
exists (a script reload), in exactly the same way. A script that ends early —
the player logged out mid-`sleep2` — never leaves a frozen shell behind.

### `population_spawn("<map>", <x>, <y>, <job>{, <base level>{, "<name>"{, <sex>{, <flags>}}}})`

Makes one shell, for a character that has to be a particular someone: a
rival, a card hunter, a mentor. `<job>` is an id or a name (`"Wizard"`,
`"High Priest"`); its gear, stats and skills come from that job's population
profile, exactly as an ambient spawn's do, so a job with no profile is
refused.

- `(0, 0)` picks a random cell on the map; a blocked cell moves to a free one
  nearby.
- `<base level>` 0 keeps the profile's roll. Any other level is clamped to the
  profile's band.
- `"<name>"` must not belong to anyone online. `""` keeps a generated one.
- `<sex>` is `SEX_FEMALE`, `SEX_MALE`, or `-1` (the default) to choose. A Bard
  is male whatever you ask.
- Flag `1` keeps it as an ordinary ambient shell once released, instead of
  logging it out.

It arrives **already held by your NPC for 60 seconds**; extend that with
`population_hold`. It counts toward the population limit, not toward the
map's own headcount. Returns its unit id, or 0.

### `population_despawn(<gid>{, <style>})`

Takes a shell out of the world on the next tick: style `0` as a logout (it
just goes), `1` with the teleport-out effect of a fly or butterfly wing. Any
shell but a companion, held or not. Returns 1, or 0 when it is not a shell or
is a companion.

### `population_whisperevent(<gid>, "<npc>::<label>")`

While your NPC holds the shell, a whisper to it runs that label instead of a
canned reply, with the whisperer attached and two variables set:

| | |
|---|---|
| `@shell_gid` | the shell that was whispered |
| `@shell_msg$` | what was said |

`""` turns it off. A held shell with no whisper event does not answer
whispers at all. Releasing the hold clears it.

### `population_whisper(<gid>, "<message>")`

The shell whispers `<message>` to the attached player. Any shell, held or not.

## A scene, start to finish

```c
// Every ten minutes, a wizard near the south gate walls it off and flies away.
// (Written for this page and not yet run in game.)
-	script	gate_prank	-1,{
OnTimer600000:
	initnpctimer; // again in ten minutes
	.@n = population_shells("prontera", 156, 40, 25, .@gid);
	for (.@i = 0; .@i < .@n; .@i++)
		if (readparam(Class, rid2name(.@gid[.@i])) == Job_Wizard && population_hold(.@gid[.@i], 90000))
			break;
	if (.@i == .@n) end;
	.@w = .@gid[.@i];
	unitwalk .@w, 156, 44;
	sleep 6000;
	unitskillusepos .@w, "WZ_ICEWALL", 5, 156, 40;
	sleep 1500;
	unittalk .@w, rid2name(.@w) + " : lol";
	emotion ET_HNG, .@w;
	sleep 3000;
	population_despawn .@w, 1;  // fly-wings off before anyone catches them
	end;
OnInit:
	initnpctimer;
	end;
}
```

## What is not here

- **Picking up a particular item, or speaking on a channel** have no stock
  command and no shell command yet.
- **Ambient behaviour** — shells logging out on their own, emotes when hit,
  fewer of them at night — is the engine's business, not a script's.
