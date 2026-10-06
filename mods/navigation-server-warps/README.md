# Server warps for navigation

The navigation window routes between maps over the links in your own client:
kRO's warp portals, plus the NPCs that move you (sailors, signposts, airship
steps). This server places its portals from rAthena's scripts, so in
pre-renewal towns, which differ from kRO's renewal ones, and on maps a mod adds,
those routes lead to the wrong place or nowhere.

With this mod on, routes use the server's portals instead: the `warp` and
`warp2` lines in the scripts the server loads for your era, the stock scripts
other mods switch on (`stock-npc.txt`), and the scripts other mods ship. A
portal a mod switches off with `disablenpc "<name>"` is left out, so a mod that
reroutes a gate is routed over correctly.

Your client's other links stay: a sailor or a signpost is a script that warps
you when spoken to, which cannot be read the way a portal can. Its precomputed
route distances, which describe its own portals, are set aside, so routes take
the fewest maps.

`warp-index.tsv` lists the pinned rAthena's portals, which live in the server
image rather than on your machine. It is generated from the pin with the app's
server mods applied, and regenerated whenever the rAthena pin moves (CI fails
until it is):

```
scripts/navigation-index.sh
```
