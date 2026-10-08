#!/usr/bin/env python3
"""Regenerate the rebellion mod's tables from rAthena and three CSV files.

    python3 registry/tools/rebellion/build.py --rathena ../rathena            # rewrite them
    python3 registry/tools/rebellion/build.py --rathena ../rathena --check    # fail if stale

The work is done by registry/tools/expanded_class/expanded_class.py; this file
only describes the class. docs/mods/EXPANDED_CLASS_REBIRTH.md is the guide.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "expanded_class"))
import expanded_class as ec  # noqa: E402

ec.run(ec.config(
    __file__,
    MOD_NAME="rebellion",
    JOBS=("Rebellion",),
    ITEM_JOB="Rebellion",             # the item_db Jobs: key (EAJ_REBELLION)
    BASE="Gunslinger",
    SKILL_PREFIX="RL_",
    # Rebellion sits a little below a transcendent class. Pre-renewal's Sniper
    # gets the Hunter HP table times 1.25; Rebellion gets it times 1.1. SP
    # follows the Gunslinger's table.
    HP_FROM="Sniper", HP_SCALE=1.10,
    SP_FROM="Gunslinger", SP_SCALE=1.10,
    EXP_FROM="Sniper",
    # Renewal's job bonuses come to +37 by job 60. These three more make +40,
    # five below a transcendent class's +45.
    EXTRA_BONUS=[(56, "Dex"), (58, "Agi"), (60, "Luk")],
    BONUS_TOTAL=40,
    MAX_JOB_LEVEL=60,
    # Renewal's skills consume these, and pre-renewal's item tables do not
    # have them. Sanctified_Bullet and Silver_Bullet_ are bullets Platinum
    # Alter names as required equipment; one missing item makes rAthena reject
    # the whole entry.
    NEW_FROM_RENEWAL=["Full_Metal_Jacket", "Shooting_Mine", "Dragon_Tail_Missile", "Slug_Bullet",
                      "Sanctified_Bullet", "Silver_Bullet_"],
    # Pre-renewal has no fixed cast time and DEX shortens every cast to
    # nothing at 150; 75% of renewal's fixed cast becomes after-cast delay,
    # which DEX does not touch, and the rest is added to the cast time.
    FIXED_CAST_TO_DELAY=0.75,
    WEAPON_KINDS={
        "revolver": dict(type="Weapon", sub="Revolver", loc=["Right_Hand"], label="Revolver", unid="Gun"),
        "rifle":    dict(type="Weapon", sub="Rifle",    loc=["Both_Hand"],  label="Rifle", unid="Gun"),
        "gatling":  dict(type="Weapon", sub="Gatling",  loc=["Both_Hand"],  label="Gatling Gun", unid="Gun"),
        "shotgun":  dict(type="Weapon", sub="Shotgun",  loc=["Both_Hand"],  label="Shotgun", unid="Gun"),
        "grenade":  dict(type="Weapon", sub="Grenade",  loc=["Both_Hand"],  label="Grenade Launcher", unid="Gun"),
    },
))
