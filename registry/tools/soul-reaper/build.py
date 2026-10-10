#!/usr/bin/env python3
"""Regenerate the soul-reaper mod's tables from rAthena and three CSV files.

    python3 registry/tools/soul-reaper/build.py --rathena ../rathena            # rewrite them
    python3 registry/tools/soul-reaper/build.py --rathena ../rathena --check    # fail if stale

The work is done by registry/tools/expanded_class/expanded_class.py; this file
only describes the class. docs/mods/EXPANDED_CLASS_REBIRTH.md is the guide
(section 11 covers third classes).

Soul Reaper is a third class in rAthena, on top of Soul Linker. Here it is
the Soul Linker's transcendent form: reborn Novice -> Taekwon -> Soul Reaper,
to job 70, 127 skill points like any transcendent class. rAthena already lets
it wear what a Soul Linker wears and, in a pre-renewal build, the
transcendent-only items too; so no item gets a job flag.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "expanded_class"))
import expanded_class as ec  # noqa: E402

ec.run(ec.config(
    __file__,
    MOD_NAME="soul-reaper",
    JOBS=("Soul_Reaper",),
    BASE="Soul_Linker",
    SKILL_PREFIX="SP_",
    # A little below a transcendent class: a transcendent class gets its
    # second class's HP table times 1.25 (its upper flag); this gets the Soul
    # Linker's times 1.1.
    HP_FROM="Soul_Linker", HP_SCALE=1.10,
    SP_FROM="Soul_Linker", SP_SCALE=1.10,
    EXP_FROM="Sniper",                # the transcendent base and job EXP tables
    # Renewal's bonuses come to +43 by job 70; its last three are dropped for
    # +40, five below a transcendent class's +45.
    BONUS_TOTAL=40,
    MAX_JOB_LEVEL=70,
    # The equipment is for Soul Reapers only: a Soul Linker's Jobs: key, and
    # Classes: Third, which a Soul Linker is not.
    EQUIP_JOBS=["SoulLinker"], EQUIP_CLASSES=["Third"],
    # Pre-renewal has no fixed cast time and DEX shortens every cast to
    # nothing at 150; 75% of renewal's fixed cast becomes after-cast delay,
    # which DEX does not touch, and the rest is added to the cast time.
    FIXED_CAST_TO_DELAY=0.75,
    WEAPON_KINDS={
        "staff": dict(type="Weapon", sub="Staff", loc=["Right_Hand"], label="Staff", unid="Rod"),
    },
))
