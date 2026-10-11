# patches/rathena

Hooks in rAthena's own files that a mod needs before the fork has them.
`scripts/apply-server-mods.sh` applies them, in order, to the rAthena commit
`config/VENDOR_PINS` pins (once per checkout; a stamp file marks it). Each is
written to become a commit on the fork's `ragnarokoffline` branch; when the pin
moves to a commit that contains one, delete its patch here.

| Patch | What it adds | Off by default? |
|---|---|---|
| `0001-skill-damage-level-extension` | The `skill_damage_level` server extension: the skill formulas that read a player's base level or job level directly (Dragon Breath, Gates of Hell, Heal, Esma, Enchant Blade, Zangetsu ...; `doc/extensions.md` lists them) ask a helper, which with the extension on caps the base level at `base_level` and fixes the job level at `job_level` | yes: the extension is off, and then the helper returns the real level |
| `0002-lua-level-and-job-level-hooks` | Lua `level` and `job_level` hooks: `skill("SR_GATEOFHELL", { level = function(c, stock) return math.min(stock, 99) end })`. The same helper asks them, per skill, after the extension | yes: with no hook registered the formula reads the real level |
| `0003-lua-heal-hook` | A Lua `heal` hook for `AL_HEAL`, `AB_HIGHNESSHEAL` and `AB_CHEAL`: the amount restored, with `c.base` the amount before Coluceo Heal's bonus per party member | yes: with no hook registered heals are stock |

The Lua API is described in the block comment at the top of
`src/map/skill_lua.hpp` (in the patched tree).
