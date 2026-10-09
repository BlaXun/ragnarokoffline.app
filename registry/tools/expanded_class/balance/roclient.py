#!/usr/bin/env python3
"""Headless rAthena client for the test rig (packetver 20221005, stdlib only).

Logs in login -> char -> map, creates the character if the account has none,
enters the map and runs a command script. Every line it prints is JSON.

    python3 roclient.py --user gmtest --pass gmtest123 run cmds.txt
    python3 roclient.py --user gmtest --pass gmtest123 run -        # commands from stdin
    python3 roclient.py --user gmtest --pass gmtest123 do 'say @jobchange 4211' 'wait 2'

Commands (one per line, '#' starts a comment):
    say <text>                    public chat; @commands work for GM accounts
    whisper <name> <text>         whisper; 'whisper npc:<NpcName> a#b' fires that NPC's OnWhisperGlobal
    wait <sec>                    stay logged in for <sec>, printing text events (command/NPC replies)
    wait-for <regex> [sec]        wait until a text event (chat, system message, NPC dialog,
                                  whisper, broadcast) matches; prints it, or a timeout event
    dump-damage <sec>             print damage/skill events (JSON lines) as they arrive for <sec>
    dump-events <sec> [ev,...]    the same for every event, or only the listed kinds
    clear                         forget collected events (dump-* only print new ones anyway)
    mobs                          print the monsters currently in sight
    units                         print every unit in sight (players, NPCs, mobs)
    self                          print own id, position, HP/SP
    attack <target> [once]        melee/auto-attack; target = <id> | nearest | mob:<class id>
    stop-attack
    skill <skill_id> <lv> [target] skill on a unit; target = self (default) | <id> | nearest | mob:<class>
    skill-pos <skill_id> <lv> <x> <y>
    walk <x> <y>
    talk <id|name>                click an NPC (name: a substring of what is in sight)
    skillup <skill_id> [n]        raise a skill n times with skill points
    menu <n>                      queue the answer for the next NPC select() (1-based; 255 = cancel)
    select-skill <id>             answer a skill selection list (Auto Shadow Spell)
    input <value>                 queue the answer for the next NPC input
    echo <text>
    quit

Event kinds: text, damage, skill_damage, skill_nodamage, skill_cast, skill_fail,
hp, unit_hp, vanish, status, spawn, job, mapmove, npc_menu, npc_input, unknown_packet.
"""

import argparse
import json
import os
import re
import shlex
import socket
import struct
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# Packet obfuscation keys by packetver. rAthena's clif_obfuscation.hpp sets all
# three to 0 for every client after 2018-03-07, so for 20221005 the XOR is a
# no-op; the cycling is implemented anyway so --keys can test an older build.
OBFUSCATION_KEYS = {20221005: (0, 0, 0)}

# Fallback lengths for packets the generated table does not know.
EXTRA_LEN = {}

# What `wait` prints: the replies to @commands and NPCs, and anything that breaks the session.
TEXT_KINDS = {"text", "npc_menu", "skill_select", "npc_input", "disconnected", "unknown_packet", "parse_error"}

# Damage types (e_damage_type) worth naming in the output.
DMG_TYPES = {0: "normal", 1: "pickup", 2: "sitdown", 3: "standup", 4: "endure", 5: "splash",
             6: "single", 7: "repeat", 8: "multi_hit", 9: "multi_hit_endure", 10: "critical",
             11: "lucky", 12: "touch", 13: "multi_hit_critical"}


def cstr(b):
	return b.split(b"\0", 1)[0].decode("latin-1", "replace")


def decode_posdir(b):
	x = (b[0] << 2) | (b[1] >> 6)
	y = ((b[1] & 0x3F) << 4) | (b[2] >> 4)
	return x, y


def decode_movedata(b):
	x1 = ((b[2] & 0x0F) << 6) | (b[3] >> 2)
	y1 = ((b[3] & 0x03) << 8) | b[4]
	return x1, y1


def encode_posdir(x, y, d=0):
	return bytes([(x >> 2) & 0xFF, ((x << 6) | ((y >> 4) & 0x3F)) & 0xFF, ((y << 4) | (d & 0x0F)) & 0xFF])


class Conn:
	"""A framed connection: reads whole packets using the generated length table."""

	def __init__(self, host, port, lens, keys=(0, 0, 0)):
		self.sock = socket.create_connection((host, port), timeout=10)
		self.sock.settimeout(None)
		self.buf = b""
		self.lens = lens
		self.keys = keys
		self.key = keys[0]
		self.lock = threading.Lock()

	def send(self, data, obfuscate=False):
		with self.lock:
			if obfuscate and any(self.keys):
				self.key = (self.key * self.keys[1] + self.keys[2]) & 0xFFFFFFFF
				cmd = struct.unpack_from("<H", data)[0] ^ ((self.key >> 16) & 0x7FFF)
				data = struct.pack("<H", cmd) + data[2:]
			self.sock.sendall(data)

	def recv_exact(self, n):
		while len(self.buf) < n:
			chunk = self.sock.recv(65536)
			if not chunk:
				raise ConnectionError("connection closed by server")
			self.buf += chunk
		out, self.buf = self.buf[:n], self.buf[n:]
		return out

	def recv_packet(self):
		head = self.recv_exact(2)
		cmd = struct.unpack("<H", head)[0]
		ln = self.lens.get(cmd, EXTRA_LEN.get(cmd))
		if ln is None:
			raise UnknownPacket(cmd, head + self.buf[:64])
		if ln == -1:
			rest = self.recv_exact(2)
			ln = struct.unpack("<H", rest)[0]
			return cmd, head + rest + self.recv_exact(ln - 4)
		return cmd, head + self.recv_exact(ln - 2)

	def close(self):
		try:
			self.sock.close()
		except OSError:
			pass


class UnknownPacket(Exception):
	def __init__(self, cmd, data):
		super().__init__(f"unknown packet 0x{cmd:04x}")
		self.cmd = cmd
		self.data = data


class Client:
	def __init__(self, args):
		self.args = args
		table = json.load(open(args.pktlen))
		self.lens = {int(k, 16): v for k, v in table["len"].items()}
		self.names = {int(k, 16): v for k, v in table["name"].items()}
		self.t0 = time.time()
		self.events = []
		self.deadline = None
		self.cv = threading.Condition()
		self.units = {}
		self.me = {}
		self.menu_queue = []
		self.input_queue = []
		self.map = None
		self.alive = True
		self.logf = open(args.log, "a") if args.log else None

	# --- output ---------------------------------------------------------------

	def out(self, obj):
		print(json.dumps(obj), flush=True)

	def event(self, ev, **kw):
		e = {"t": round(time.time() - self.t0, 3), "ev": ev, **kw}
		if ev == "text":                     # the test helper's give#: remember the unequipped copy
			m = re.search(r"KoTest: idx (\d+) id \d+ equip=0\b", kw.get("text") or "")
			if m:
				self.given = int(m.group(1))
		with self.cv:
			self.events.append(e)
			self.cv.notify_all()
		if self.logf:
			self.logf.write(json.dumps(e) + "\n")
			self.logf.flush()
		if self.args.events:
			self.out(e)
		return e

	# --- login / char ---------------------------------------------------------

	def login(self):
		a = self.args
		for attempt in range(10):
			c = Conn(a.host, a.login_port, self.lens)
			c.send(struct.pack("<HI24s24sB", 0x64, a.packetver, a.user.encode(), a.password.encode(), 0))
			cmd, p = c.recv_packet()
			c.close()
			# SC_NOTIFY_BAN 8: the previous session of this account is still being saved; retry
			if cmd == 0x81 and p[2] == 8 and attempt < 9:
				time.sleep(1.5)
				continue
			break
		if cmd == 0x81:
			raise SystemExit(json.dumps({"ev": "error", "stage": "login", "ban_code": p[2]}))
		if cmd == 0x83E:
			raise SystemExit(json.dumps({"ev": "error", "stage": "login", "refused": struct.unpack_from("<I", p, 2)[0], "unblock": cstr(p[6:26])}))
		if cmd != 0xAC4:
			raise SystemExit(json.dumps({"ev": "error", "stage": "login", "packet": f"0x{cmd:04x}"}))
		self.login_id1, self.aid, self.login_id2 = struct.unpack_from("<III", p, 4)
		self.sex = p[46]
		n = (len(p) - 47) // 160
		off = len(p) - n * 160
		ip = socket.inet_ntoa(p[off:off + 4])
		port = struct.unpack_from("<H", p, off + 4)[0]
		self.out({"ev": "login_ok", "aid": self.aid, "sex": self.sex, "char_server": f"{ip}:{port}"})
		return ip, port

	def parse_char(self, b):
		return {
			"cid": struct.unpack_from("<I", b, 0)[0],
			"job": struct.unpack_from("<h", b, 84)[0],
			"base_level": struct.unpack_from("<h", b, 92)[0],
			"name": cstr(b[108:132]),
			"slot": b[138],
			"map": cstr(b[142:158]),
		}

	def char_select(self, ip, port):
		a = self.args
		if ip.startswith("0.") or ip == "0.0.0.0":
			ip = a.host
		c = Conn(ip, port, self.lens)
		c.send(struct.pack("<HIIIHB", 0x65, self.aid, self.login_id1, self.login_id2, 0, self.sex))
		c.recv_exact(4)  # the char server echoes the account id, unframed
		chars = None
		c.sock.settimeout(5)
		try:
			while True:
				cmd, p = c.recv_packet()
				if cmd == 0x6B:
					chars = [self.parse_char(p[27 + i * 175:27 + (i + 1) * 175]) for i in range((len(p) - 27) // 175)]
				elif cmd == 0x6C:
					raise SystemExit(json.dumps({"ev": "error", "stage": "char", "refused": p[2]}))
				elif cmd == 0x20D:  # block list, the last packet of the char list burst
					break
				elif cmd == 0x8B9 and struct.unpack_from("<H", p, 10)[0] != 0:  # 0 = passed
					raise SystemExit(json.dumps({"ev": "error", "stage": "char", "msg": "pincode requested; set pincode_enabled: no"}))
		except socket.timeout:
			pass
		c.sock.settimeout(None)
		chars = chars or []
		self.out({"ev": "char_list", "chars": chars})
		want = a.char
		pick = None
		for ch in chars:
			if (want and ch["name"].lower() == want.lower()) or (not want and ch["slot"] == a.slot):
				pick = ch
		if pick is None:
			name = want or ("Rig" + re.sub(r"[^A-Za-z0-9]", "", a.user).capitalize())[:23]
			used = {ch["slot"] for ch in chars}
			slot = a.slot if a.slot not in used else min(set(range(9)) - used)
			c.send(struct.pack("<H24sBHHIB", 0xA39, name.encode(), slot, 1, 1, 0, self.sex))
			cmd, p = c.recv_packet()
			while cmd == 0x8B9:  # pincode state "passed"
				cmd, p = c.recv_packet()
			if cmd != 0xB6F:
				raise SystemExit(json.dumps({"ev": "error", "stage": "make_char", "packet": f"0x{cmd:04x}", "code": p[2] if len(p) > 2 else None}))
			pick = self.parse_char(p[2:])
			self.out({"ev": "char_created", **pick})
		c.send(struct.pack("<HB", 0x66, pick["slot"]))
		while True:
			cmd, p = c.recv_packet()
			if cmd == 0xAC5:
				break
			if cmd in (0x6C, 0x840):
				raise SystemExit(json.dumps({"ev": "error", "stage": "select_char", "packet": f"0x{cmd:04x}"}))
		self.cid = struct.unpack_from("<I", p, 2)[0]
		mapname = cstr(p[6:22])
		mip = socket.inet_ntoa(p[22:26])
		mport = struct.unpack_from("<H", p, 26)[0]
		self.char_conn = c  # rAthena drops the char session on its own once the map takes over
		self.me.update(name=pick["name"], cid=self.cid, job=pick["job"])
		self.out({"ev": "char_selected", "name": pick["name"], "cid": self.cid, "map": mapname, "map_server": f"{mip}:{mport}"})
		return mip, mport

	# --- map ------------------------------------------------------------------

	def map_enter(self, ip, port):
		a = self.args
		self.mc = Conn(a.host if ip.startswith("0.") else ip, port, self.lens, a.keys)
		tick = int((time.time() - self.t0) * 1000) & 0xFFFFFFFF
		self.mc.send(struct.pack("<HIIIIIB", 0x436, self.aid, self.cid, self.login_id1, tick, 0, self.sex), obfuscate=True)
		while True:
			cmd, p = self.mc.recv_packet()
			if cmd == 0x2EB:
				x, y = decode_posdir(p[6:9])
				self.me.update(id=self.aid, x=x, y=y)
				break
			if cmd == 0x283:
				continue
			if cmd in (0x74, 0x81, 0x840):
				raise SystemExit(json.dumps({"ev": "error", "stage": "map", "packet": f"0x{cmd:04x}", "data": p.hex()}))
		self.mc.send(struct.pack("<H", 0x7D), obfuscate=True)  # CZ_NOTIFY_ACTORINIT / LoadEndAck
		threading.Thread(target=self.reader, daemon=True).start()
		threading.Thread(target=self.ticker, daemon=True).start()
		self.out({"ev": "map_entered", "aid": self.aid, "x": self.me["x"], "y": self.me["y"]})

	def send(self, data):
		self.mc.send(data, obfuscate=True)

	def ticker(self):
		while self.alive:
			time.sleep(10)
			try:
				self.send(struct.pack("<HI", 0x360, int((time.time() - self.t0) * 1000) & 0xFFFFFFFF))
			except OSError:
				return

	def reader(self):
		try:
			while self.alive:
				cmd, p = self.mc.recv_packet()
				try:
					self.handle(cmd, p)
				except struct.error as e:
					self.event("parse_error", packet=f"0x{cmd:04x}", error=str(e), data=p[:64].hex())
		except UnknownPacket as e:
			self.event("unknown_packet", packet=f"0x{e.cmd:04x}", data=e.data.hex(),
			           note="no length known; add it to EXTRA_LEN in roclient.py. Connection is now out of sync.")
		except (ConnectionError, OSError) as e:
			if self.alive:
				self.event("disconnected", reason=str(e))
		self.alive = False
		with self.cv:
			self.cv.notify_all()

	def unit_name(self, uid):
		u = self.units.get(uid)
		return u.get("name") if u else None

	def handle(self, cmd, p):
		u16 = lambda o: struct.unpack_from("<H", p, o)[0]
		i16 = lambda o: struct.unpack_from("<h", p, o)[0]
		u32 = lambda o: struct.unpack_from("<I", p, o)[0]
		i32 = lambda o: struct.unpack_from("<i", p, o)[0]

		if cmd == 0x8C8:  # ZC_NOTIFY_ACT
			typ = p[29]
			self.event("damage", src=u32(2), target=u32(6), skill=0, damage=i32(22), damage2=i32(30),
			           sp_damage=bool(p[26]), div=u16(27), type=typ, type_name=DMG_TYPES.get(typ, str(typ)),
			           src_delay=i32(14), dmg_delay=i32(18))
		elif cmd == 0x1DE:  # ZC_NOTIFY_SKILL
			typ = p[32]
			self.event("skill_damage", skill=u16(2), src=u32(4), target=u32(8), damage=i32(24), level=i16(28),
			           div=i16(30), type=typ, type_name=DMG_TYPES.get(typ, str(typ)), src_delay=i32(16), dmg_delay=i32(20))
		elif cmd == 0x115:  # ZC_NOTIFY_SKILL_POSITION
			self.event("skill_damage", skill=u16(2), src=u32(4), target=u32(8), damage=i16(28), level=i16(30),
			           div=i16(32), type=p[34], x=i16(24), y=i16(26))
		elif cmd == 0x9CB:  # ZC_USE_SKILL: no-damage skill (heal amount / level in 'value')
			self.event("skill_nodamage", skill=u16(2), value=i32(4), target=u32(8), src=u32(12), success=bool(p[16]))
		elif cmd == 0xB1A:  # ZC_USESKILL_ACK: cast bar
			self.event("skill_cast", src=u32(2), target=u32(6), x=u16(10), y=u16(12), skill=u16(14),
			           element=u32(16), cast_ms=u32(20))
		elif cmd == 0x117:  # ZC_NOTIFY_GROUNDSKILL
			self.event("skill_ground", skill=u16(2), src=u32(4), level=i16(8), x=i16(10), y=i16(12))
		elif cmd == 0x110:  # ZC_ACK_TOUSESKILL
			self.event("skill_fail", skill=u16(2), btype=i32(4), item=u32(8), flag=p[12], cause=p[13])
		elif cmd == 0x139:
			self.event("attack_out_of_range", target=u32(2))
		elif cmd == 0x977:  # ZC_HP_INFO
			self.event("unit_hp", id=u32(2), hp=i32(6), max_hp=i32(10))
			if u32(2) in self.units:
				self.units[u32(2)].update(hp=i32(6), max_hp=i32(10))
		elif cmd in (0xB0, 0xACB):  # ZC_PAR_CHANGE / ZC_LONGLONGPAR_CHANGE
			var = u16(2)
			val = i32(4) if cmd == 0xB0 else struct.unpack_from("<q", p, 4)[0]
			key = {5: "hp", 6: "max_hp", 7: "sp", 8: "max_sp", 11: "base_level", 55: "job_level"}.get(var)
			if key:
				self.me[key] = val
				if key in ("hp", "sp"):
					self.event("hp", id=self.aid, **{key: val})
		elif cmd == 0x1D7:  # ZC_SPRITE_CHANGE: look type 0 is the job
			if u32(2) == self.aid and p[6] == 0:
				self.me["job"] = i32(7)
				self.event("job", id=self.aid, job=i32(7))
		elif cmd == 0xB1:  # ZC_LONGPAR_CHANGE (zeny, exp, ...)
			pass
		elif cmd == 0x80:  # ZC_NOTIFY_VANISH
			uid, typ = u32(2), p[6]
			if typ == 1:
				self.event("vanish", id=uid, type="died", name=self.unit_name(uid))
			self.units.pop(uid, None)
		elif cmd in (0x9FD, 0x9FE, 0x9FF):  # unit walking / spawn / idle
			uid = u32(5)
			n = len(p)
			unit = {"id": uid, "objtype": p[4], "class": i16(23), "name": cstr(p[n - 24:]),
			        "max_hp": i32(n - 35), "hp": i32(n - 31), "boss": p[n - 27]}
			if cmd == 0x9FD:
				unit["x"], unit["y"] = decode_movedata(p[n - 47:n - 41])
			elif cmd == 0x9FE:
				unit["x"], unit["y"] = decode_posdir(p[n - 44:n - 41])
			else:
				unit["x"], unit["y"] = decode_posdir(p[n - 45:n - 42])
			new = uid not in self.units
			self.units.setdefault(uid, {}).update(unit)
			if new and cmd == 0x9FE:
				self.event("spawn", **unit)
		elif cmd == 0x86:  # ZC_NOTIFY_MOVE
			if u32(2) in self.units:
				x, y = decode_movedata(p[6:12])
				self.units[u32(2)].update(x=x, y=y)
		elif cmd == 0x88:  # ZC_STOPMOVE
			if u32(2) == self.aid:
				self.me.update(x=u16(6), y=u16(8))
			elif u32(2) in self.units:
				self.units[u32(2)].update(x=u16(6), y=u16(8))
		elif cmd == 0x87:  # ZC_NOTIFY_PLAYERMOVE
			x, y = decode_movedata(p[6:12])
			self.me.update(x=x, y=y)
		elif cmd == 0x91:  # ZC_NPCACK_MAPMOVE: the client must ack the new map
			self.map = cstr(p[2:18])
			self.me.update(map=self.map, x=u16(18), y=u16(20))
			self.units.clear()
			self.send(struct.pack("<H", 0x7D))
			self.event("mapmove", map=self.map, x=u16(18), y=u16(20))
		elif cmd in (0x983, 0x43F, 0x196):  # status change on/off
			if cmd == 0x983:
				self.event("status", type=u16(2), id=u32(4), on=bool(p[8]), total_ms=u32(9), remain_ms=i32(13),
				           val1=i32(17), val2=i32(21), val3=i32(25))
			elif cmd == 0x43F:
				self.event("status", type=u16(2), id=u32(4), on=bool(p[8]), remain_ms=i32(9),
				           val1=i32(13), val2=i32(17), val3=i32(21))
			else:
				self.event("status", type=u16(2), id=u32(4), on=bool(p[8]))
		# --- text ---
		elif cmd == 0x8E:
			self.event("text", kind="self", text=cstr(p[4:]))
		elif cmd == 0x8D:
			self.event("text", kind="chat", id=u32(4), text=cstr(p[8:]))
		elif cmd == 0x9A:
			self.event("text", kind="broadcast", text=cstr(p[4:]))
		elif cmd == 0x1C3:
			self.event("text", kind="broadcast", text=cstr(p[16:]))
		elif cmd == 0x2C1:
			self.event("text", kind="npc_chat", id=u32(4), text=cstr(p[12:]))
		elif cmd == 0x9DE:
			self.event("text", kind="whisper", sender=cstr(p[8:32]), text=cstr(p[33:]))
		elif cmd == 0x9DF:
			self.event("whisper_ack", result=p[2])
		elif cmd == 0x291:
			self.event("text", kind="msgstringtable", msg_id=u16(2))
		elif cmd == 0x9CD:
			self.event("text", kind="msgstringtable", msg_id=u16(2), color=u32(4))
		# --- NPC dialog: answered automatically so a script never hangs on the client ---
		elif cmd == 0xB4:
			self.event("text", kind="npc", npc=u32(4), text=cstr(p[8:]))
		elif cmd == 0xB5:
			self.send(struct.pack("<HI", 0xB9, u32(2)))
		elif cmd == 0xB6:
			self.send(struct.pack("<HI", 0x146, u32(2)))
		elif cmd == 0xB7:
			opts = cstr(p[8:]).split(":")
			choice = self.menu_queue.pop(0) if self.menu_queue else 255
			self.event("npc_menu", npc=u32(4), options=opts, chose=choice)
			self.send(struct.pack("<HIB", 0xB8, u32(4), choice))
		elif cmd == 0x442:  # ZC_SKILL_SELECT_REQUEST: Auto Shadow Spell's list
			n = (struct.unpack_from("<H", p, 2)[0] - 8) // 2
			self.event("skill_select", flag=struct.unpack_from("<i", p, 4)[0], skills=list(struct.unpack_from(f"<{n}h", p, 8)))
		elif cmd == 0x142:
			val = int(self.input_queue.pop(0)) if self.input_queue else 0
			self.event("npc_input", npc=u32(2), kind="number", value=val)
			self.send(struct.pack("<HIi", 0x143, u32(2), val))
		elif cmd == 0x1D4:
			val = str(self.input_queue.pop(0)) if self.input_queue else ""
			self.event("npc_input", npc=u32(2), kind="string", value=val)
			b = val.encode() + b"\0"
			self.send(struct.pack("<HHI", 0x1D5, 8 + len(b), u32(2)) + b)
		elif self.args.trace:
			self.event("packet", packet=f"0x{cmd:04x}", name=self.names.get(cmd), len=len(p))

	# --- commands -------------------------------------------------------------

	def resolve_target(self, spec):
		if spec in (None, "self", "me"):
			return self.aid
		if spec.isdigit():
			return int(spec)
		mobs = [u for u in self.units.values() if u.get("objtype") == 5]
		if spec.startswith("mob:"):
			cls = int(spec[4:])
			mobs = [u for u in mobs if u.get("class") == cls]
		elif spec != "nearest":
			raise ValueError(f"bad target {spec!r}")
		if not mobs:
			raise ValueError(f"no monster in sight for {spec!r}")
		mx, my = self.me.get("x", 0), self.me.get("y", 0)
		return min(mobs, key=lambda u: max(abs(u["x"] - mx), abs(u["y"] - my)))["id"]

	def stream(self, seconds, kinds):
		"""Print events of the given kinds that arrive during the next <seconds>."""
		with self.cv:
			start = len(self.events)
		end = time.time() + seconds
		idx = start
		while True:
			with self.cv:
				while idx >= len(self.events) and time.time() < end and self.alive:
					self.cv.wait(max(0.0, end - time.time()))
				batch = self.events[idx:]
				idx = len(self.events)
			for e in batch:
				if kinds is None or e["ev"] in kinds:
					self.out(e)
			if time.time() >= end or not self.alive:
				return

	def wait_for(self, pattern, timeout):
		rx = re.compile(pattern)
		end = time.time() + timeout
		with self.cv:
			idx = len(self.events)
			while time.time() < end and self.alive:
				for e in self.events[idx:]:
					if e["ev"] == "text" and rx.search(e.get("text", "")):
						self.out({**e, "matched": pattern})
						return True
				idx = len(self.events)
				self.cv.wait(max(0.0, end - time.time()))
		self.out({"ev": "timeout", "waiting_for": pattern})
		return False

	def wait_skill(self, skill, timeout):
		"""Wait until one of my casts of SKILL lands, fails or reports success."""
		end = time.time() + timeout
		with self.cv:
			idx = len(self.events)
			while time.time() < end and self.alive:
				for e in self.events[idx:]:
					if e["ev"] in ("damage", "skill_damage", "skill_nodamage", "skill_fail"):
						self.out(e)              # reported as dump-damage would
					if e.get("skill") == skill and e["ev"] in ("skill_damage", "skill_nodamage", "skill_fail") \
							and (e["ev"] == "skill_fail" or e.get("src") == self.aid):
						return True
				idx = len(self.events)
				self.cv.wait(max(0.0, end - time.time()))
		return False

	def _mine(self, e, skill):
		return e.get("skill") == skill and (e["ev"] == "skill_fail" or e.get("src") == self.aid)

	def cast(self, send, skill, timeout):
		"""Cast SKILL once, as a player would: send the request; when neither a
		cast bar nor a hit answers within 0.35 s the server refused it (still
		in after-cast delay), so send it again; once it is cast, wait for it to
		land. A request is never repeated during a cast, which would restart it."""
		end = time.time() + timeout
		while time.time() < end and self.alive:
			if self.deadline and time.time() > self.deadline:
				return
			with self.cv:
				idx = len(self.events)
			send()
			started = None
			try_end = time.time() + 0.35
			with self.cv:
				while time.time() < try_end and started is None:
					for e in self.events[idx:]:
						if e["ev"] in ("damage", "skill_damage", "skill_nodamage", "skill_fail"):
							self.out(e)
						if started is None and self._mine(e, skill) and e["ev"] in ("skill_cast", "skill_damage", "skill_nodamage", "skill_fail"):
							started = e
					idx = len(self.events)
					if started is None:
						self.cv.wait(max(0.0, try_end - time.time()))
			if started is None:
				continue
			if started["ev"] != "skill_cast":
				return
			with self.cv:
				while time.time() < end and self.alive:
					for e in self.events[idx:]:
						if e["ev"] in ("damage", "skill_damage", "skill_nodamage", "skill_fail"):
							self.out(e)
						if self._mine(e, skill) and e["ev"] in ("skill_damage", "skill_nodamage", "skill_fail"):
							return
					idx = len(self.events)
					self.cv.wait(max(0.0, end - time.time()))
			return

	def say(self, text):
		b = f"{self.me['name']} : {text}".encode() + b"\0"
		self.send(struct.pack("<HH", 0xF3, 4 + len(b)) + b)

	def run_line(self, line):
		line = line.strip()
		if not line or line.startswith("#"):
			return True
		cmd, _, rest = line.partition(" ")
		rest = rest.strip()
		if self.deadline and time.time() > self.deadline and cmd in ("skill", "skill-pos", "attack", "cast", "cast-pos"):
			return True                      # past the deadline: the run is over
		if cmd == "say":
			self.say(rest)
		elif cmd == "whisper":
			parts = shlex.split(rest)
			target = parts[0]
			msg = rest[rest.index(parts[0]) + len(parts[0]):].strip() if not rest.startswith('"') else " ".join(parts[1:])
			b = msg.encode() + b"\0"
			self.send(struct.pack("<HH24s", 0x96, 28 + len(b), target.encode()) + b)
		elif cmd == "wait":
			self.stream(float(rest or 1), TEXT_KINDS)
		elif cmd in ("cast", "cast-pos"):
			# cast <skill_id> <lv> <target>  /  cast-pos <skill_id> <lv> <x> <y>: one cast, landed
			parts = rest.split()
			inner = ("skill " if cmd == "cast" else "skill-pos ") + rest
			self.cast(lambda: self.run_line(inner), int(parts[0]), 20)
		elif cmd == "wait-skill":
			# wait-skill <skill_id> [sec]: until my cast of it lands or fails
			parts = rest.split()
			if not (self.deadline and time.time() > self.deadline):
				self.wait_skill(int(parts[0]), float(parts[1]) if len(parts) > 1 else 15)
		elif cmd == "deadline":
			# deadline <sec>: from now on, skip skill and wait commands once SEC have passed
			self.deadline = time.time() + float(rest)
		elif cmd == "wait-for":
			parts = shlex.split(rest)
			ok = self.wait_for(parts[0], float(parts[1]) if len(parts) > 1 else 10)
			if not ok and self.args.strict:
				return False
		elif cmd == "dump-damage":
			self.stream(float(rest or 5), {"damage", "skill_damage", "skill_nodamage", "skill_cast", "skill_fail",
			                               "vanish", "attack_out_of_range"})
		elif cmd == "dump-events":
			parts = rest.split()
			self.stream(float(parts[0]) if parts else 5, set(parts[1].split(",")) if len(parts) > 1 else None)
		elif cmd == "clear":
			with self.cv:
				self.events.clear()
		elif cmd == "mobs":
			for u in self.units.values():
				if u.get("objtype") == 5:
					self.out({"ev": "mob", **u})
		elif cmd == "units":
			for u in self.units.values():
				self.out({"ev": "unit", **u})
		elif cmd == "self":
			self.out({"ev": "self", "aid": self.aid, **self.me})
		elif cmd == "attack":
			parts = rest.split()
			tid = self.resolve_target(parts[0] if parts else "nearest")
			self.send(struct.pack("<HIB", 0x437, tid, 0 if "once" in parts else 7))
			self.out({"ev": "cmd", "attack": tid})
		elif cmd == "stop-attack":
			self.send(struct.pack("<H", 0x118))
		elif cmd == "skill":
			parts = rest.split()
			tid = self.resolve_target(parts[2] if len(parts) > 2 else "self")
			self.send(struct.pack("<HHHI", 0x438, int(parts[1]), int(parts[0]), tid))
			self.out({"ev": "cmd", "skill": int(parts[0]), "level": int(parts[1]), "target": tid})
		elif cmd == "skill-pos":
			s, lv, x, y = map(int, rest.split())
			self.send(struct.pack("<HHHHH", 0x366, lv, s, x, y))
		elif cmd == "walk":
			x, y = map(int, rest.split())
			self.send(struct.pack("<H", 0x35F) + encode_posdir(x, y))
		elif cmd == "talk":
			# talk <id> | <name substring>: click an NPC (CZ_CONTACTNPC)
			if rest.isdigit():
				tid = int(rest)
			else:
				hits = [u for u in self.units.values() if rest.lower() in (u.get("name") or "").lower()]
				if not hits:
					self.out({"ev": "error", "talk": rest, "error": "no such unit in sight"})
					return self.alive
				tid = hits[0]["id"]
			self.send(struct.pack("<HIB", 0x90, tid, 1))
			self.out({"ev": "cmd", "talk": tid})
		elif cmd == "wear":
			# wear <server inventory idx> <position mask>: equip as the client does (CZ_REQ_WEAR_EQUIP)
			idx, pos = (int(x, 0) for x in rest.split())
			self.send(struct.pack("<HHI", 0x998, idx + 2, pos))
		elif cmd == "wear-given":
			# wear-given <position mask>: wear the item the test helper's give# last handed out
			if getattr(self, "given", None) is None:
				self.out({"ev": "error", "wear-given": "no give# seen"})
			else:
				self.send(struct.pack("<HHI", 0x998, self.given + 2, int(rest, 0)))
		elif cmd == "use":
			# use <server inventory idx>: use an item, as the client does (CZ_USE_ITEM2)
			self.send(struct.pack("<HHI", 0x439, int(rest.split()[0]) + 2, self.aid))
		elif cmd == "select-skill":
			# select-skill <skill_id>: answer ZC_SKILL_SELECT_REQUEST (CZ_SKILL_SELECT_RESPONSE)
			self.send(struct.pack("<Hih", 0x443, 1, int(rest.split()[0])))
		elif cmd == "skillup":
			# skillup <skill_id> [times]: spend skill points (CZ_UPGRADE_SKILLLEVEL)
			parts = rest.split()
			for _ in range(int(parts[1]) if len(parts) > 1 else 1):
				self.send(struct.pack("<HH", 0x112, int(parts[0])))
				time.sleep(0.05)
		elif cmd == "menu":
			self.menu_queue.append(int(rest))
		elif cmd == "input":
			self.input_queue.append(rest)
		elif cmd == "echo":
			self.out({"ev": "echo", "text": rest})
		elif cmd == "quit":
			return False
		else:
			self.out({"ev": "error", "unknown_command": cmd})
		return self.alive

	def run(self, lines):
		ip, port = self.login()
		ip, port = self.char_select(ip, port)
		self.map_enter(ip, port)
		self.stream(self.args.settle, set())  # let the initial burst arrive before the first command
		ok = True
		for line in lines:
			try:
				if not self.run_line(line):
					# quit ends cleanly; a failed --strict wait-for or a lost connection does not
					ok = line.strip() == "quit"
					break
			except (ValueError, IndexError) as e:
				self.out({"ev": "error", "line": line.strip(), "error": str(e)})
				if self.args.strict:
					ok = False
					break
		if not self.alive:
			self.out({"ev": "error", "error": "disconnected from map server"})
			ok = False
		self.alive = False
		self.mc.close()
		return ok


def main():
	ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	ap.add_argument("--host", default="127.0.0.1")
	ap.add_argument("--login-port", type=int, default=16900)
	ap.add_argument("--user", required=True)
	ap.add_argument("--pass", dest="password", required=True)
	ap.add_argument("--char", help="character name to select (created if missing)")
	ap.add_argument("--slot", type=int, default=0)
	ap.add_argument("--packetver", type=int, default=20221005)
	ap.add_argument("--keys", type=lambda s: tuple(int(k, 0) for k in s.split(",")), default=None,
	                help="obfuscation keys k1,k2,k3 (default: rAthena's for --packetver)")
	ap.add_argument("--pktlen", default=os.path.join(HERE, "pktlen.json"), help="generated by tools/gen_pktlen.sh")
	ap.add_argument("--log", default=None, help="append every event as JSON here (default logs/client-<user>.jsonl)")
	ap.add_argument("--events", action="store_true", help="print every event as it arrives")
	ap.add_argument("--trace", action="store_true", help="also record packets the client does not interpret")
	ap.add_argument("--settle", type=float, default=1.5, help="seconds to wait after entering the map")
	ap.add_argument("--strict", action="store_true", help="stop and exit 1 on a failed wait-for or a bad command")
	sub = ap.add_subparsers(dest="mode", required=True)
	r = sub.add_parser("run", help="run a command file ('-' = stdin)")
	r.add_argument("file")
	d = sub.add_parser("do", help="run commands given as arguments")
	d.add_argument("commands", nargs="+")
	args = ap.parse_args()
	if args.keys is None:
		args.keys = OBFUSCATION_KEYS.get(args.packetver, (0, 0, 0))
	if args.log is None:
		os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
		args.log = os.path.join(HERE, "logs", f"client-{args.user}.jsonl")
	if args.mode == "run":
		lines = sys.stdin if args.file == "-" else open(args.file)
	else:
		lines = args.commands
	sys.exit(0 if Client(args).run(lines) else 1)


if __name__ == "__main__":
	main()
