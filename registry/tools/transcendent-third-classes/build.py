#!/usr/bin/env python3
"""Regenerate the transcendent-third-classes mod's tables from rAthena and three CSV files.

    python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena            # rewrite them
    python3 registry/tools/transcendent-third-classes/build.py --rathena ../rathena --check    # fail if stale

The work is done by registry/tools/expanded_class/expanded_class.py; this file
only describes the classes. docs/mods/EXPANDED_CLASS_REBIRTH.md is the guide.

A renewal third class here is a SIDEGRADE of the transcendent second class:
a reborn first class chooses one or the other, permanently. The class is
rAthena's transcendent third class (it keeps the transcendent HP bonus and
gear), but its skill tree is renewal's non-transcendent one: the third
class's own skills and what came before the second class, never the
transcendent class's skills. Tables are the transcendent class's own, so
the two differ only in their skills; damage is measured to parity.

Classes so far: Guillotine Cross (instead of Assassin Cross), Shadow Chaser
(instead of Stalker). Each class keeps its CSV files in its own directory.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "expanded_class"))
import expanded_class as ec  # noqa: E402

WEAPONS = {
    "katar":  dict(type="Weapon", sub="Katar",  loc=["Both_Hand"],  label="Katar",  unid="Katar"),
    "dagger": dict(type="Weapon", sub="Dagger", loc=["Right_Hand"], label="Dagger", unid="Dagger"),
    "bow":    dict(type="Weapon", sub="Bow",    loc=["Both_Hand"],  label="Bow",    unid="Bow"),
}

# Shared by every class: the transcendent class's job levels and bonus total,
# and the fixed cast time rule (docs/mods/EXPANDED_CLASS_REBIRTH.md, section 7).
COMMON = dict(MOD_NAME="transcendent-third-classes", BONUS_TOTAL=45, MAX_JOB_LEVEL=70,
              EQUIP_CLASSES=["Upper"], FIXED_CAST_TO_DELAY=0.75, WEAPON_KINDS=WEAPONS)

guillotine_cross = ec.config(
    __file__, **COMMON,
    JOBS=("Guillotine_Cross_T",),
    # Renewal's Guillotine Cross tree: Novice, Thief, Assassin and the 19 GC
    # skills; renewal's transcendent one also inherits Assassin Cross.
    TREE_FROM={"Guillotine_Cross_T": "Guillotine_Cross"},
    BASE="Assassin_Cross",
    SKILL_PREFIX="GC_",
    # Parity with the Assassin Cross: its own HP, SP and EXP tables. The class
    # is transcendent in rAthena, so it gets the same 125% HP bonus.
    HP_FROM="Assassin_Cross", HP_SCALE=1.0,
    SP_FROM="Assassin_Cross", SP_SCALE=1.0,
    EXP_FROM="Assassin_Cross",
    # Renewal's Guillotine Cross bonuses come to +43 by job 70; two more make
    # a transcendent class's +45.
    EXTRA_BONUS=[(68, "Agi"), (70, "Str")],
    # Its weapons suit both of the Assassin's transcendent paths: an
    # Assassin's Jobs: key and Classes: Upper, which a third class also meets.
    EQUIP_JOBS=["Assassin"],
    EQUIP_LABEL="Assassin Cross or Guillotine Cross",
    ITEMS_ABOUT="The Guillotine Cross's weapons, from guillotine_cross/equipment.csv.",
    CSV_DIR="guillotine_cross",
    # Cross Impact: renewal spams it twice a second; here it is the heavy hit.
    SKILL_OVERRIDES={"GC_CROSSIMPACT": {"AfterCastActDelay": "1500"}},
)

shadow_chaser = ec.config(
    __file__, **COMMON,
    JOBS=("Shadow_Chaser_T",),
    # Renewal's Shadow Chaser tree: Novice, Thief, Rogue and the SC skills;
    # renewal's transcendent one also inherits Stalker (Preserve, Full Strip).
    TREE_FROM={"Shadow_Chaser_T": "Shadow_Chaser"},
    BASE="Stalker",
    SKILL_PREFIX="SC_",
    HP_FROM="Stalker", HP_SCALE=1.0,
    SP_FROM="Stalker", SP_SCALE=1.0,
    EXP_FROM="Stalker",
    # Renewal's Shadow Chaser bonuses come to +43 by job 70; two more make +45.
    EXTRA_BONUS=[(68, "Dex"), (70, "Agi")],
    EQUIP_JOBS=["Rogue"],
    EQUIP_LABEL="Stalker or Shadow Chaser",
    ITEMS_ABOUT="The Shadow Chaser's weapons, from shadow_chaser/equipment.csv.",
    CSV_DIR="shadow_chaser",
    # Auto Shadow Spell casts copied Mage and Wizard spells. These four more
    # can be copied, aim at the target and cost no item; rAthena skips Holy
    # Light and Magnus Exorcismus in auto-casts, and the self-centred and
    # catalyst ninjutsu would not place or would cast for free.
    SKILL_FLAGS_ADD={"IsAutoShadowSpell": ["PR_TURNUNDEAD", "NJ_KOUENKA", "NJ_HYOUSENSOU", "NJ_HUUJIN"]},
)

ec.run([guillotine_cross, shadow_chaser])
