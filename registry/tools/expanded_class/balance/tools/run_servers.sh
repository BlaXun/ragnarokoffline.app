#!/bin/bash
# Runs inside the rorig-server container (host network). One log per server.
# rAthena redraws progress lines with \r; turn those into newlines so the logs grep cleanly.
cd /rathena
unr() { python3 -u -c 'import sys
for l in sys.stdin: sys.stdout.write(l.replace("\r", "\n"))'; }
./login-server 2>&1 | unr > /logs/login.log &
sleep 1
./char-server 2>&1 | unr > /logs/char.log &
sleep 1
./map-server 2>&1 | unr > /logs/map.log &
wait -n
echo "[rig] a server exited; stopping the rest" | tee -a /logs/map.log
pkill -f -- '-server$' 2>/dev/null; kill $(jobs -p) 2>/dev/null
wait
