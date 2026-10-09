#!/usr/bin/env bash
# Stop the test servers.
#   ./down.sh          stop login/char/map (database keeps running, characters persist)
#   ./down.sh --db     also stop the database container (data kept)
#   ./down.sh --wipe   also delete the database container (next ./up.sh re-imports the schema)
set -euo pipefail
docker rm -f rorig-server >/dev/null 2>&1 && echo "servers stopped" || echo "servers were not running"
case "${1:-}" in
	--db)   docker stop rorig-db >/dev/null 2>&1 && echo "database stopped" ;;
	--wipe) docker rm -f rorig-db >/dev/null 2>&1 && echo "database deleted" ;;
esac
