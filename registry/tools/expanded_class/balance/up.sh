#!/usr/bin/env bash
# Install zero or more mod directories into the pre-re test server and (re)start it.
#
#   ./up.sh [mod_dir ...]
#
# Each mod_dir may contain:
#   db/**        -> rathena/db/import/**, each file replacing the import stub of that name
#                   (item_db.yml, mob_db.yml, skill_db.yml, skill_tree.yml, job_stats.yml, extension_db.yml, ...)
#   lua/*.lua    -> rathena/db/import/lua/       (load.txt too, if the mod ships one)
#   npc/**.txt   -> rathena/npc/rigmod/<mod>/    and an `npc:` line per file in conf/import/map_conf.txt
#   conf/*.txt   -> appended to rathena/conf/import/<same name>  (battle_conf.txt, map_conf.txt, ...)
#
# Every run starts from pristine import dirs (copied from the *-tmpl folders), so a
# mod removed from the command line is really gone. The database persists; ./down.sh --wipe resets it.
set -euo pipefail
RIG="$(cd "$(dirname "$0")" && pwd)"
# One build/up at a time: two makes in the same tree corrupt each other's objects.
if [ -z "${RIG_LOCKED:-}" ]; then
	exec 9>"$RIG/.lock"
	flock -n 9 || { echo "waiting for another build.sh/up.sh on this rig to finish..."; flock 9; }
	export RIG_LOCKED=1
fi
RA="$RIG/rathena"
LOGS="$RIG/logs"
mkdir -p "$LOGS"

[ -x "$RA/map-server" ] || "$RIG/build.sh"

# --- stop a running server -------------------------------------------------
docker rm -f rorig-server >/dev/null 2>&1 || true

# --- database --------------------------------------------------------------
if ! docker ps --format '{{.Names}}' | grep -qx rorig-db; then
	if docker ps -a --format '{{.Names}}' | grep -qx rorig-db; then
		docker start rorig-db >/dev/null
	else
		docker run -d --name rorig-db -p 127.0.0.1:13306:3306 \
			-e MARIADB_ROOT_PASSWORD=rootpw -e MARIADB_DATABASE=ragnarok \
			-e MARIADB_USER=ragnarok -e MARIADB_PASSWORD=ragnarok mariadb:11.4 >/dev/null
	fi
fi
sql() { docker exec -i rorig-db mariadb -uragnarok -pragnarok ragnarok "$@"; }
for _ in $(seq 60); do sql -e 'SELECT 1' >/dev/null 2>&1 && break; sleep 1; done
if ! sql -N -e "SHOW TABLES LIKE 'login'" | grep -q login; then
	echo "importing schema (main.sql, logs.sql, roulette_default_data.sql)"
	sql < "$RA/sql-files/main.sql"
	sql < "$RA/sql-files/logs.sql"
	sql < "$RA/sql-files/roulette_default_data.sql"
fi
# main.sql is all CREATE TABLE IF NOT EXISTS: replaying it adds the tables a newer
# checkout introduced (e.g. mod_store) to an existing database; its seed INSERTs
# fail as duplicates, which --force skips.
sql --force < "$RA/sql-files/main.sql" >/dev/null 2>&1 || true
sql < "$RIG/base/sql/accounts.sql"

# --- import dirs: pristine, then rig settings, then mods --------------------
rm -rf "$RA/conf/import" "$RA/db/import" "$RA/npc/rigmod"
cp -r "$RA/conf/import-tmpl" "$RA/conf/import"
cp -r "$RA/db/import-tmpl" "$RA/db/import"
mkdir -p "$RA/db/import/lua" "$RA/npc/rigmod"
: > "$RA/.rig_installed"
for f in "$RIG"/base/conf/*.txt; do
	{ echo; cat "$f"; } >> "$RA/conf/import/$(basename "$f")"
done

for mod in "$@"; do
	mod="$(cd "$mod" && pwd)"
	name="$(basename "$mod")"
	echo "installing mod: $name ($mod)"
	if [ -d "$mod/db" ]; then
		# Each file replaces the import stub of the same name (item_db.yml, mob_db.yml,
		# skill_db.yml, skill_tree.yml, job_stats.yml, ...): the import layer is a whole file.
		while read -r rel; do
			dst="$RA/db/import/$rel"
			if grep -qxF "$rel" "$RA/.rig_installed" 2>/dev/null; then
				note="REPLACES the copy from an earlier mod on this command line"
			elif [ -e "$RA/db/import-tmpl/$rel" ]; then
				note="replaces import stub"
			else
				note="new file (no import stub of this name; check rAthena reads it)"
			fi
			mkdir -p "$(dirname "$dst")"
			if grep -qxF "$rel" "$RA/.rig_installed" 2>/dev/null && grep -q '^Body:' "$mod/db/$rel"; then
				# like the app: one header, both mods' entries
				note="merged with the copy from an earlier mod"
				sed -n '/^Body:/,$p' "$mod/db/$rel" | tail -n +2 >> "$dst"
			else
				cp "$mod/db/$rel" "$dst"
			fi
			echo "$rel" >> "$RA/.rig_installed"
			echo "  db/import/$rel  ($note)"
		done < <(cd "$mod/db" && find . -type f | sed "s|^\./||" | sort)
	fi
	if [ -d "$mod/lua" ]; then
		cp -r "$mod/lua/." "$RA/db/import/lua/"
		(cd "$mod/lua" && find . -type f | sed "s|^\./|  db/import/lua/|")
	fi
	if [ -d "$mod/npc" ]; then
		mkdir -p "$RA/npc/rigmod/$name"
		cp -r "$mod/npc/." "$RA/npc/rigmod/$name/"
		echo "// rig mod: $name" >> "$RA/conf/import/map_conf.txt"
		(cd "$RA" && find "npc/rigmod/$name" -type f -name '*.txt' | sort) | while read -r f; do
			echo "npc: $f" >> "$RA/conf/import/map_conf.txt"
			echo "  $f"
		done
	fi
	if [ -d "$mod/conf" ]; then
		for f in "$mod"/conf/*.txt; do
			[ -e "$f" ] || continue
			{ echo; echo "// rig mod: $name"; cat "$f"; } >> "$RA/conf/import/$(basename "$f")"
			echo "  conf/import/$(basename "$f") (appended)"
		done
	fi
done

# --- start -----------------------------------------------------------------
: > "$LOGS/login.log"; : > "$LOGS/char.log"; : > "$LOGS/map.log"
docker run -d --name rorig-server --network host --user "$(id -u):$(id -g)" \
	-v "$RA:/rathena" -v "$LOGS:/logs" -v "$RIG/tools:/tools:ro" \
	rorig-build /tools/run_servers.sh >/dev/null

echo -n "waiting for map-server"
for _ in $(seq 180); do
	if grep -q "Server is 'ready'" "$LOGS/map.log" 2>/dev/null && grep -q "Map-Server .* connected\|Map-server .* connected\|map-server.*connected" -i "$LOGS/char.log" 2>/dev/null; then
		break
	fi
	if ! docker ps --format '{{.Names}}' | grep -qx rorig-server; then
		echo; echo "server container exited; tail of logs:"; tail -n 30 "$LOGS"/{login,char,map}.log; exit 1
	fi
	echo -n .; sleep 1
done
echo
if ! grep -q "Server is 'ready'" "$LOGS/map.log"; then
	echo "map-server not ready after 180s; see $LOGS/map.log"; exit 1
fi
echo "up: login 127.0.0.1:16900  char :16121  map :15121  db :13306"
n_err=$(grep -c "\[Error\]" "$LOGS/map.log" || true)
n_warn=$(grep -c "\[Warning\]" "$LOGS/map.log" || true)
echo "map.log: $n_err errors, $n_warn warnings ($LOGS/map.log)"
echo "--- import entries loaded (non-zero):"
grep -E "Done reading '[1-9][0-9]*' entries in '(db/import|conf/import)" "$LOGS/map.log" | sort -u || true
echo "--- errors / warnings (with 2 lines of context), Lua and npc/rigmod lines:"
# (the two stock-config warnings every start prints are left out: s1/p1 and mesitemicon)
grep -n -A2 -E "^\[(Error|Warning)\]|Lua|npc/rigmod" "$LOGS/map.log" \
	| grep -v -E "^--$|s1/p1|inter-server user/password|conf/map_athena.conf \(or|mesitemicon" | head -n 80 || true
