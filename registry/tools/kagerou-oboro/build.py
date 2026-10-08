#!/usr/bin/env python3
"""Regenerate the kagerou-oboro mod's tables from rAthena and three CSV files.

    python3 registry/tools/kagerou-oboro/build.py --rathena ../rathena            # rewrite them
    python3 registry/tools/kagerou-oboro/build.py --rathena ../rathena --check    # fail if stale

The work is done by registry/tools/expanded_class/expanded_class.py; this file
only describes the class. docs/mods/EXPANDED_CLASS_REBIRTH.md is the guide.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "expanded_class"))
import expanded_class as ec  # noqa: E402

ec.run(ec.config(
    __file__,
    MOD_NAME="kagerou-oboro",
    JOBS=("Kagerou", "Oboro"),
    ITEM_JOB="KagerouOboro",          # the item_db Jobs: key (EAJ_KAGEROUOBORO)
    BASE="Ninja",
    SKILL_PREFIX=("KO_", "OB_", "KG_"),
    # Kagerou and Oboro sit a little below a transcendent class. Pre-renewal's
    # Assassin Cross gets the Assassin HP table times 1.25; these get it times
    # 1.1. SP follows the Ninja's table, which is already the deeper one.
    HP_FROM="Assassin_Cross", HP_SCALE=1.10,
    SP_FROM="Ninja", SP_SCALE=1.10,
    EXP_FROM="Assassin_Cross",
    # Renewal's job bonuses stop at job level 50; these continue them to 60 and
    # total +40, five below a transcendent class's +45.
    EXTRA_BONUS=[(52, "Str"), (54, "Agi"), (56, "Dex"), (58, "Luk"), (60, "Int")],
    BONUS_TOTAL=40,
    MAX_JOB_LEVEL=60,
    ASPD={"Fist": 400, "Dagger": 500, "Huuma": 700},   # the Ninja's, with a quicker Huuma
    # Kunai Splash's damage is added outside the skill's percentage
    # (battle.cpp, KO_HAPPOKUNAI), so the Lua ratio hook cannot scale it; with
    # renewal's 0.5 s delay it did about four times Sonic Blow's damage per
    # second, to everything around. Sonic Blow's 2 s delay brings it below
    # Meteor Assault.
    SKILL_OVERRIDES={"KO_HAPPOKUNAI": {"AfterCastActDelay": "2000"}},
    # Pre-renewal has no fixed cast time and DEX shortens every cast to
    # nothing at 150; 75% of renewal's fixed cast becomes after-cast delay,
    # which DEX does not touch, and the rest is added to the cast time. Skills
    # with a 10 s+ cooldown keep it all as cast time (Izayoi halves it).
    FIXED_CAST_TO_DELAY=0.75,
    WEAPON_KINDS={
        "huuma":  dict(type="Weapon", sub="Huuma",  loc=["Both_Hand"],  label="Huuma Shuriken", unid="Huuma Shuriken"),
        "dagger": dict(type="Weapon", sub="Dagger", loc=["Right_Hand"], label="Dagger",         unid="Dagger"),
    },
))
