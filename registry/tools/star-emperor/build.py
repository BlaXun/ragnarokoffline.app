#!/usr/bin/env python3
"""Regenerate the star-emperor mod's tables from rAthena and three CSV files.

    python3 registry/tools/star-emperor/build.py --rathena ../rathena            # rewrite them
    python3 registry/tools/star-emperor/build.py --rathena ../rathena --check    # fail if stale

The work is done by registry/tools/expanded_class/expanded_class.py; this file
only describes the class. docs/mods/EXPANDED_CLASS_REBIRTH.md is the guide.

Star Emperor is a third class in rAthena, on top of Star Gladiator. Here it
is the Star Gladiator's transcendent form: reborn Novice -> Taekwon -> Star
Emperor, to job 70, 127 skill points like any transcendent class. rAthena
already lets it wear what a Star Gladiator wears, and, in a pre-renewal
build, the transcendent-only items too; so no item gets a job flag.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "expanded_class"))
import expanded_class as ec  # noqa: E402

ec.run(ec.config(
    __file__,
    MOD_NAME="star-emperor",
    # Star_Emperor2 is the Union (SG_FUSION) form, with its own tree.
    JOBS=("Star_Emperor", "Star_Emperor2"),
    BASE="Star_Gladiator",
    SKILL_PREFIX="SJ_",
    # A little below a transcendent class: a transcendent class gets its
    # second class's HP table times 1.25 (its upper flag); this gets the Star
    # Gladiator's times 1.1.
    HP_FROM="Star_Gladiator", HP_SCALE=1.10,
    SP_FROM="Star_Gladiator", SP_SCALE=1.10,
    EXP_FROM="Sniper",                # the transcendent base and job EXP tables
    # Renewal's bonuses come to +43 by job 70; its last three are dropped for
    # +40, five below a transcendent class's +45.
    BONUS_TOTAL=40,
    MAX_JOB_LEVEL=70,
    # The equipment is for Star Emperors only: a Star Gladiator's Jobs: key,
    # and Classes: Third, which a Star Gladiator is not.
    EQUIP_JOBS=["StarGladiator"], EQUIP_CLASSES=["Third"],
    # Pre-renewal has no fixed cast time and DEX shortens every cast to
    # nothing at 150; 75% of renewal's fixed cast becomes after-cast delay,
    # which DEX does not touch, and the rest is added to the cast time.
    FIXED_CAST_TO_DELAY=0.75,
    WEAPON_KINDS={
        "book": dict(type="Weapon", sub="Book", loc=["Right_Hand"], label="Book", unid="Book"),
    },
))
