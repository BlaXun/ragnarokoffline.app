# blaze-shield-knockback

Make Blaze Shield pillars hit on entry and pin the mob until the pillar
burns out, so no cell in the mob's path can be skipped. One line in
[`db/extension_db.yml`](db/extension_db.yml) that flips the server-side
`blaze_shield_knockback` extension on.

## What it does

Stock KAENSIN pillars only damage via the 100 ms global `skill_unit_timer`:
a mob fast enough to cross a cell between global ticks skips it entirely,
and the field feels unreliable. With the mod on:

- **Entry hit.** Walking onto a pillar fires the pillar's damage loop right
  then, so even a 50 ms/cell mob can't blow past a cell untouched.
- **Pin on hit.** After the entry hit, the mob is held in place by a
  skill-induced walkdelay sized to the pillar's remaining burn time
  (`val2 * interval`). The mob eats the full stack of hits for that
  pillar, then can walk off and start on the next one.
- **Endure escape hatch.** A mob under `SC_ENDURE` (and bosses with
  `MD_STATUSIMMUNE`) skip the pin — they still eat the entry hit but can
  keep walking. Same escape hatch stock firewall-family cells have.

Scoped to `NJ_KAENSIN`. Fire Wall, Lava Slide, and other placed magic
skills are untouched. No knockback — mobs stay on the cell they walked
onto rather than being shoved around.

## Verifying

Cast Blaze Shield in a corridor and send a Poring through. With the mod
off: the Poring often walks across the field and only 1–2 pillars show
damage numbers. With the mod on: the Poring stops on the first pillar
it steps on, eats the full `(skill_lv+1)/2 + 4` hits, moves to the next
pillar, repeats. A fast mob (e.g. an Eggyra) gets the same treatment —
every pillar on its path is hit at least once at entry.

## Requires

App 1.3.10 or newer — the version that vendored the rAthena fork's
extensions framework and the `blaze_shield_knockback` gate itself. See
[docs/MODDING.md → db/extension_db.yml](../../docs/MODDING.md) for how a
mod flips a server extension on through `db/import/`.

## Applying it

`db/` is read when the server starts. Settings → Restart server is
enough — no app restart, no rebuild.
