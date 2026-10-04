# Pre-renewal skill descriptions, by Sandalphon

Sandalphon's "Improved Pre-Renewal Skill Translations and Tooltips", revised
January 13, 2025, packaged as a mod. The text is theirs, unchanged:
<https://rathena.org/board/topic/139880-pre-renewal-skill-translations-and-tooltips-improved-revised-re-edited-and-commented-by-sandalphon/>

They started from llchrisll's pre-renewal skill translation. Then they checked
each skill against iROwiki Classic, RateMyServer and rAthena's source:

- damage formulas;
- debuff success chances;
- per-level scaling;
- which stats and gear apply.

They also re-wrapped the lines so words are not split.

## What it changes

One client file: `data/luafiles514/lua files/skillinfoz/skilldescript.lub`,
the text in the skill description window. It does not touch skill names,
the skill tree or anything on the server.

It covers the same 1,035 skills as the app's stock pre-renewal table, and every
skill it names is defined in the client's `skillid.lub`. It is pre-renewal only.
Renewal skills work differently, so on a renewal server the app does not load it.

Report mistakes in the text to Sandalphon on the topic above.
