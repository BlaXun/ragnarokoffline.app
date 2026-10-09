#!/usr/bin/env bash
# Generate $RIG/pktlen.json: packet id -> length (-1 = variable) for the built
# PACKETVER, measured from the server's own headers with the map-server's -D flags:
#   1. sizeof every PACKET_<X> whose HEADER_<X> exists (common/ and map/ packets.hpp)
#      -- variable-length when the struct has a length member;
#   2. sizeof the struct clif.cpp sends under each packet_headers enum value
#      (packets_struct.hpp: idle_unitType, sendLookType, skillscale, ...);
#   3. gaps only: clif_packetdb.hpp / clif_shuffle.hpp lengths (often stale for
#      server->client packets, which is why they never override 1-2), then raw
#      WFIFOHEAD(fd,N); WFIFOW(fd,0)=0x.. writes in src/map/*.cpp.
set -euo pipefail
RIG="$(cd "$(dirname "$0")/.." && pwd)"
docker run --rm --user "$(id -u):$(id -g)" -v "$RIG/rathena:/rathena" -v "$RIG/tools:/tools" -w /rathena/src/map rorig-build bash -c '
set -e
FLAGS=$(sed -n "s/.*-DHAS_TLS \(.*-DHAVE_MONOTONIC_CLOCK\).*/\1/p" Makefile | head -1)
INC="-I. -I../common -I.. -I../../3rdparty/libconfig -I../../3rdparty/rapidyaml/src -I../../3rdparty/rapidyaml/ext/c4core/src -I/usr/include/mysql"
# map/packets.hpp and common/packets.hpp share the PACKETS_HPP include guard,
# so the char/login structs (common) are measured in a translation unit of their own.
printf "#include \"clif.hpp\"\n#include \"packets.hpp\"\n" > /tmp/hdr_map.cpp
printf "#include <common/packets.hpp>\n" > /tmp/hdr_common.cpp
# Drop their own packet()/parseable_packet() macros so ours (print the length) apply.
sed -E "/#[[:space:]]*(define|undef)[[:space:]]+(packet|parseable_packet)\b/d" clif_packetdb.hpp > /tmp/packetdb.inc
sed -E "/#[[:space:]]*(define|undef)[[:space:]]+(packet|parseable_packet)\b/d" clif_shuffle.hpp > /tmp/shuffle.inc
# enum header -> struct, from how clif.cpp fills them in
python3 - > /tmp/enum_pairs <<PY
import re
src = open("clif.cpp").read()
hdr = open("packets_struct.hpp").read()
hdr = hdr[hdr.index("enum packet_headers"):]
enums = set(re.findall(r"\b(\w+)\s*=\s*0x", hdr[:hdr.index("};")]))
seen = set()
for m in re.finditer(r"(?:struct\s+)?((?:PACKET|packet)_\w+)\s*\*?\s*(\w+)\s*(?:\{\}|=|;)", src):
    seg = src[m.end():m.end() + 3000]
    mm = re.search(r"\b" + m.group(2) + r"\s*(?:\.|->)\s*[Pp]acket[Tt]ype\s*=\s*(\w+)\s*;", seg)
    if mm and mm.group(1) in enums and not m.group(1).startswith("PACKET_CZ_") and (mm.group(1), m.group(1)) not in seen:
        seen.add((mm.group(1), m.group(1)))
        print(mm.group(1), m.group(1))
PY
gen() { # <header tu> <with packetdb/enums>
	echo "#include <cstdio>"
	echo "#include <type_traits>"
	cat "$1"
	# Variable-length when a length member (any of the spellings rAthena uses) exists.
	for f in packetLength PacketLength packetSize packetLen; do
		echo "template<class T, class = void> struct has_$f : std::false_type {};"
		echo "template<class T> struct has_$f<T, std::void_t<decltype(&T::$f)>> : std::true_type {};"
	done
	echo "template<class T> constexpr int varlen() { return has_packetLength<T>::value || has_PacketLength<T>::value || has_packetSize<T>::value || has_packetLen<T>::value; }"
	echo "int main(){"
	g++ -std=c++17 $FLAGS $INC -E -dD "$1" | sed -n "s/^const int16 HEADER_\([A-Za-z0-9_]*\) = .*/\1/p" | sort -u | while read n; do
		echo "  printf(\"st %d %d %d $n\\n\", (int)(uint16)HEADER_$n, (int)sizeof(PACKET_$n), varlen<PACKET_$n>());"
	done
	if [ "$2" = 1 ]; then
		while read e s; do
			echo "  printf(\"en %d %d %d $s\\n\", (int)(uint16)$e, (int)sizeof($s), varlen<$s>());"
		done < /tmp/enum_pairs
		echo "#define packet(cmd,length) printf(\"db %d %d\\n\", (int)(cmd), (int)(int16)(length))"
		echo "#define parseable_packet(cmd,length,func,...) printf(\"db %d %d\\n\", (int)(cmd), (int)(int16)(length))"
		echo "#include \"/tmp/packetdb.inc\""
		echo "#include \"/tmp/shuffle.inc\""
	fi
	echo "return 0; }"
}
: > /tools/pktlen.raw
: > /tmp/dropped
for tu in common map; do
	db=0; [ $tu = map ] && db=1
	gen /tmp/hdr_$tu.cpp $db > /tmp/sizes.cpp
	# Any line that does not compile under this PACKETVER (struct named differently,
	# or not defined for this version) is dropped.
	g++ -std=c++17 $FLAGS $INC -w -fsyntax-only /tmp/sizes.cpp 2>&1 | sed -n "s|^/tmp/sizes.cpp:\([0-9]*\):[0-9]*: error.*|\1|p" | sort -un > /tmp/badlines || true
	for l in $(cat /tmp/badlines); do sed -n "${l}p" /tmp/sizes.cpp | grep -o "[a-z][a-z] %d %d %d [A-Za-z0-9_]*" | sed "s/.* //" >> /tmp/dropped; done
	[ -s /tmp/badlines ] && sed -i "$(sed "s/$/d/" /tmp/badlines | paste -sd";")" /tmp/sizes.cpp
	g++ -std=c++17 $FLAGS $INC -w -c /tmp/sizes.cpp -o /tmp/sizes.o
	g++ /tmp/sizes.o -o /tmp/sizes -Wl,--unresolved-symbols=ignore-all
	/tmp/sizes >> /tools/pktlen.raw
done
echo "structs: $(grep -c "^st" /tools/pktlen.raw), enum headers: $(grep -c "^en" /tools/pktlen.raw), packetdb: $(grep -c "^db" /tools/pktlen.raw), dropped: $(tr "\n" " " < /tmp/dropped)"
'
python3 - "$RIG/tools/pktlen.raw" "$RIG/pktlen.json" "$RIG/rathena/src/map" <<'PY'
import glob, json, re, sys
lens, names = {}, {}
rows = [l.split() for l in open(sys.argv[1])]
for kind in ("st", "en"):
    for p in rows:
        if p[0] == kind:
            cmd = int(p[1])
            lens[cmd] = -1 if int(p[3]) else int(p[2])
            names.setdefault(cmd, p[4])
db = {}
for p in rows:
    if p[0] == "db" and int(p[1]) > 0:
        db[int(p[1])] = int(p[2])  # the server registers in order; the last one wins
for cmd, ln in db.items():
    lens.setdefault(cmd, ln)
for f in glob.glob(sys.argv[3] + "/*.cpp"):
    for m in re.finditer(r"WFIFOHEAD\(\s*\w+\s*,\s*(\d+)\s*\);\s*\n\s*WFIFOW\(\s*\w+\s*,\s*0\s*\)\s*=\s*(0x[0-9a-fA-F]+)", open(f).read()):
        lens.setdefault(int(m.group(2), 16), int(m.group(1)))
json.dump({"len": {f"0x{k:04x}": v for k, v in sorted(lens.items())},
           "name": {f"0x{k:04x}": v for k, v in sorted(names.items())}}, open(sys.argv[2], "w"), indent=0)
print(f"{len(lens)} packet lengths -> {sys.argv[2]}")
PY
