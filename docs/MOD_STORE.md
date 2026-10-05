# Mod store: data a mod keeps for itself

> **Status: proposed, not built yet.** This is the design under discussion in
> [#440](https://github.com/Flux159/ragnarokoffline.app/issues/440). The API
> below is what mods would write against. Comment on the issue before relying
> on any name here.

A mod gets a place to keep its own data, **written through the store and never
through SQL**. Scripts' `query_sql` and `query_logsql` are read-only:
they log in as a SELECT-only user that can't see `login`, which arrives in the
same release as this store at the latest.
The store lives in the world's database, in tables only the map server writes.

## Scopes

| Scope | What it's for | Loaded | Removed |
|---|---|---|---|
| **global** | the mod's own world state: a market, a leaderboard, a season | when the map server starts | only when the player deletes the mod's data |
| **account** | per account: unlocks, a rank shared by every character | when the account logs in | with the account |
| **char** | per character: quest progress, a bounty in progress | when the character logs in | with the character |

Account and character data behave like rAthena's own account (`#var`) and
character variables: loaded with the player, saved with the player, deleted
with them. So nothing is left behind, and memory follows the players who are
online, not everyone who ever played.

**A mod sees only its own store.** The namespace comes from where the calling
code was loaded (`npc/mods/<mod>/…`, `db/import/lua/<mod>/…`), not from a name
the mod passes in. There is no reading another mod's store, and the store's
tables are left out of what the read-only SQL login can see.

## Paths and values

Each scope is one document, addressed by dotted paths:

```
market.items.501.price      → 55
market.trades               → 1204
bounty.kills                → 3
season.name                 → "Autumn"
```

- **Values:** integers and strings, plus nested tables from Lua.
- **"Tables":** a path's children are its rows, enumerated with `keys`.
- **Path segments:** letters, digits and `_`, joined with `.`.

## From an NPC script

The scope comes first and can be left out for global.

```c
// global
modstore_set "market.items.501.price", 55;
.@price = modstore_get("market.items.501.price", 50);   // 50 if unset
modstore_inc "market.trades", 1;

// the attached player's character and account
modstore_set "char", "bounty.target", 1002;
modstore_inc "char", "bounty.kills", 1;
.@rank = modstore_get("account", "rank", 0);

// enumerating and ranking a "table"
.@n = modstore_keys("market.items", .@ids$);            // child names
.@n = modstore_top("leaderboard.kills", 10, .@names$, .@scores);  // highest first

if (modstore_exists("market.news"))
	modstore_delete "market.news";
```

`char` and `account` use the player attached to the script. Without one (in
`OnInit`, say), they fail with a log line, the same way `getcharid` does.

## From a Lua hook

```lua
store.inc("market.trades", 1)                      -- global
local kills = store.char.get("bounty.kills", 0)    -- the hook's player
store.char.set("bounty.kills", kills + 1)
store.account.set("unlocks.fire_relic", true)

store.set("leaderboard.kills." .. c.source.name, kills + 1)
for name, score in store.top("leaderboard.kills", 10) do ... end
```

`store.char` and `store.account` belong to the player in the hook's context.
Every call counts towards the hook's existing instruction limit.

## Querying

Queries run in memory and never block the server:

- **`keys(path)`:** a path's children.
- **`count(path)`:** how many children it has.
- **`top(path, n)`:** children sorted by their numeric value, highest first, for
  leaderboards.

A query across all characters, like "the 10 characters with the most bounty
kills", can't read offline characters' stores. Keep it in the global store as
it happens, as the Lua example does with `leaderboard.kills`.

## Limits

Limits belong to the **app**, not to rAthena or to a mod. Each release sets
them in one table in the supervisor, which writes them into the map server's
configuration at every start:

| Setting | First value | What it limits |
|---|---|---|
| `mod_store_global_bytes` | 1 MiB | one mod's global document |
| `mod_store_account_bytes` | 64 KiB | one mod's document for one account |
| `mod_store_char_bytes` | 64 KiB | one mod's document for one character |
| `mod_store_value_bytes` | 4 KiB | one string value |
| `mod_store_depth` | 8 | path segments |

So a later release can raise a limit without touching rAthena or migrating
anything. The data is the same either way; only the check on the next write
changes.

**What a mod sees:**
- **A write that would go over a limit fails, alone.** The script command
  returns `0` (Lua: `nil, "limit"`), and the map server log names the mod, the
  scope, the path and the limit. Nothing else changes and nothing crashes.
- **Reading the limits:** `modstore_limit("global")` (Lua: `store.limits()`)
  returns the current ones, so a mod can trim old entries before it runs out.
- **Needing more:** if a mod needs more than the release it targets allows, it
  says so the usual way. Say 1.6.1 raises the global limit to 2 MiB: a mod
  that needs that declares `"requires": { "app": ">=1.6.1" }`. Then 1.6.0
  refuses to install it, with a clear message, instead of letting it fail
  writes later.
- **Lowering a limit never loses data.** Limits go up, not down. If one were
  ever lowered, data already stored stays readable; writes that would grow a
  document past the new limit fail, and writes that shrink it work.

## Lifetime and backups

- **Updating a mod, or switching it off and on, keeps its data.**
- **Removing a mod keeps its data,** unless the player confirms deleting it.
  Settings → Mods gets "Reset this mod's data".
- **Backups:** everything is in the world's database, so database backups and
  restores carry it, per world.

## Why not SQL

A mod could be given its own MariaDB database, with full SQL inside it.
- **Blocking:** every query stops the map server until the database answers.
  The store answers from memory.
- **No size limits:** MariaDB can't cap a database's size, so the limits above
  couldn't be enforced.
- **Fork code:** it would need a login per mod inside rAthena, which is more
  code to carry through every upstream merge.

If the store turns out too limiting for real mods, that's the alternative to
revisit.
