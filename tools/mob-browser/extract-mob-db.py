#!/usr/bin/env python3
"""
Extract your running rAthena's mob_db.yml (renewal + pre-renewal) into the
same directory as this script (tools/), next to mob-browser.html.

Also produces a small AegisName->sprite JavaScript file that the mob browser
loads from the app's asset server, so drop-icons work when the HTML is opened
by double-click (file://) as well as when it's served over HTTP.

Cross-platform: Windows, macOS, Linux. Python 3 stdlib only.

Usage:
    python3 extract-mob-db.py              # (or `py` on Windows)

Requires the app to be running (its container engine is what we talk to).
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path


def state_paths() -> tuple[Path, Path, Path]:
    """Return (state_root, docker_socket, docker_slim_binary) for this OS."""
    system = platform.system()
    if system == "Windows":
        root = Path(os.environ.get("APPDATA", "")) / "Ragnarok Offline"
        cli = root / "runtime" / "bin" / "docker-slim.exe"
    elif system == "Darwin":
        root = Path.home() / "Library" / "Application Support" / "Ragnarok Offline"
        cli = root / "runtime" / "bin" / "docker-slim"
    else:
        root = Path.home() / ".local" / "share" / "Ragnarok Offline"
        cli = root / "runtime" / "bin" / "docker-slim"
    socket = root / "nebula" / "run" / "docker.sock"
    return root, socket, cli


def docker_host(socket_path: Path) -> str:
    """Turn the socket file into the -H value docker-slim wants.

    On Windows this file is a plain-text file holding a TCP port that
    nebulad's proxy listens on. Everywhere else it's an AF_UNIX socket
    that docker-slim connects to directly.
    """
    if platform.system() == "Windows":
        port = socket_path.read_text(encoding="utf-8").strip()
        if not port:
            raise RuntimeError("docker.sock is empty — is nebulad healthy?")
        return f"tcp://127.0.0.1:{port}"
    return f"unix://{socket_path}"


def extract(cli: Path, host: str, src: str, dst: Path) -> None:
    cp = subprocess.run(
        [str(cli), "-H", host, "cp", f"ragnarok-map:{src}", str(dst)],
        capture_output=True, text=True,
    )
    if cp.returncode != 0:
        sys.stderr.write(cp.stderr)
        sys.exit(f"docker-slim cp failed for {src}")


def scan_item_db(text: str, out: dict[str, int]) -> None:
    """Populate `out` with AegisName -> ID from an rAthena item_db yaml."""
    for m in re.finditer(r"(?:^|\n)  - Id:\s*(\d+)([\s\S]*?)(?=\n  - Id:|\Z)", text):
        item_id = int(m.group(1))
        am = re.search(r"\bAegisName:\s*(\S+)", m.group(2))
        if am:
            out[am.group(1)] = item_id


def scan_iteminfo_sprites(text: str) -> dict[int, str]:
    """Extract ID -> identifiedResourceName from a client itemInfo.lua."""
    out: dict[int, str] = {}
    for m in re.finditer(r"\[\s*(\d+)\s*\]\s*=\s*\{", text):
        item_id = int(m.group(1))
        chunk = text[m.start(): m.start() + 4000]
        rm = re.search(r"\bidentifiedResourceName\s*=\s*\"([^\"]*)\"", chunk)
        if rm and rm.group(1):
            out[item_id] = rm.group(1)
    return out


def main() -> None:
    state_root, socket, cli = state_paths()
    if not socket.exists():
        sys.exit(f"Nebula socket not found at {socket}\nIs the app running?")
    if not cli.exists():
        sys.exit(f"docker-slim not found at {cli}")

    host = docker_host(socket)
    out_dir = Path(__file__).resolve().parent
    print(f"Talking to the container engine on {host}.")

    # ---- 1. Extract raw yaml files into tools/ ----
    files = [
        ("/rathena/db/re/mob_db.yml",         "mob_db.yml"),
        ("/rathena/db/pre-re/mob_db.yml",     "mob_db_pre-re.yml"),
        ("/rathena/db/re/item_db_equip.yml",  "item_db_equip.yml"),
        ("/rathena/db/re/item_db_etc.yml",    "item_db_etc.yml"),
        ("/rathena/db/re/item_db_usable.yml", "item_db_usable.yml"),
    ]
    for src, dst_name in files:
        dst = out_dir / dst_name
        print(f"Extracting {src} -> {dst}")
        extract(cli, host, src, dst)
        print(f"  {dst.stat().st_size:,} bytes")

    # ---- 2. Build AegisName -> sprite map for drop icons ----
    print("\nBuilding AegisName -> sprite map for drop icons…")
    aegis_to_id: dict[str, int] = {}
    for name in ("item_db_equip.yml", "item_db_etc.yml", "item_db_usable.yml"):
        scan_item_db((out_dir / name).read_text(encoding="utf-8"), aegis_to_id)
    print(f"  {len(aegis_to_id):,} AegisName -> ID pairs")

    iteminfo_path = state_root / "state" / "assets" / "System" / "LuaFiles514" / "itemInfo.lua"
    if not iteminfo_path.exists():
        # SystemEN takes precedence when the English translation is on
        iteminfo_path = state_root / "state" / "assets" / "SystemEN" / "LuaFiles514" / "itemInfo.lua"
    if not iteminfo_path.exists():
        print(f"  Warning: itemInfo.lua not found — skipping icon map.")
        return
    # itemInfo.lua uses CP949 (Korean legacy) encoding by convention.
    text = iteminfo_path.read_bytes().decode("cp949", errors="replace")
    id_to_sprite = scan_iteminfo_sprites(text)
    print(f"  {len(id_to_sprite):,} ID -> sprite pairs from {iteminfo_path.name}")

    aegis_to_sprite: dict[str, str] = {}
    for aegis, item_id in aegis_to_id.items():
        sprite = id_to_sprite.get(item_id)
        if sprite:
            aegis_to_sprite[aegis] = sprite
    print(f"  {len(aegis_to_sprite):,} AegisName -> sprite pairs after join")

    # ---- 3. Publish the map as JS on the asset server ----
    # A JavaScript payload rather than raw JSON so the mob browser can pick it
    # up via <script src="..."> — cross-origin script tags don't need CORS, so
    # this works even when the HTML is opened by double-click (file://).
    assets_dir = state_root / "state" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    js_path = assets_dir / "item-icons.js"
    body = json.dumps(aegis_to_sprite, ensure_ascii=False, separators=(",", ":"))
    js_path.write_text(
        "window.__mobItemIcons=" + body +
        ";if(window.__mobItemIconsReady)window.__mobItemIconsReady();\n",
        encoding="utf-8",
    )
    print(f"  Wrote {js_path} ({js_path.stat().st_size:,} bytes)")

    print("")
    print("Done. Open tools/mob-browser.html and drop mob_db.yml into the browser once.")
    print("Drop icons will fetch from http://127.0.0.1:3338/item-icons.js automatically.")


if __name__ == "__main__":
    main()
