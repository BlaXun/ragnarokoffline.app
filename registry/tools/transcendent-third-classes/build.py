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
(instead of Stalker), Arch Bishop (instead of High Priest), Rune Knight (instead of Lord Knight),
Royal Guard (instead of Paladin), Warlock (instead of High Wizard). Each class keeps its CSV files in its own directory.

The mod also carries the expanded classes, each the rebirth of its base
class rather than a sidegrade: Kagerou and Oboro (Ninja), Rebellion
(Gunslinger), Star Emperor (Star Gladiator), Soul Reaper (Soul Linker).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "expanded_class"))
import expanded_class as ec  # noqa: E402

WEAPONS = {
    "katar":  dict(type="Weapon", sub="Katar",  loc=["Both_Hand"],  label="Katar",  unid="Katar"),
    "dagger": dict(type="Weapon", sub="Dagger", loc=["Right_Hand"], label="Dagger", unid="Dagger"),
    "bow":    dict(type="Weapon", sub="Bow",    loc=["Both_Hand"],  label="Bow",    unid="Bow"),
    "mace":   dict(type="Weapon", sub="Mace",   loc=["Right_Hand"], label="Mace",   unid="Mace"),
    "staff":  dict(type="Weapon", sub="Staff",  loc=["Right_Hand"], label="Staff",  unid="Rod"),
    "sword2": dict(type="Weapon", sub="2hSword", loc=["Both_Hand"], label="Two-Handed Sword", unid="Sword"),
    "spear2": dict(type="Weapon", sub="2hSpear", loc=["Both_Hand"], label="Two-Handed Spear", unid="Spear"),
    "spear1": dict(type="Weapon", sub="1hSpear", loc=["Right_Hand"], label="Spear", unid="Spear"),
    "staff2": dict(type="Weapon", sub="2hStaff", loc=["Both_Hand"], label="Two-Handed Staff", unid="Rod"),
    "shield": dict(type="Armor",  sub=None,      loc=["Left_Hand"],  label="Shield", unid="Shield", view=True),
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

arch_bishop = ec.config(
    __file__, **COMMON,
    JOBS=("Arch_Bishop_T",),
    # Renewal's Arch Bishop tree: Novice, Acolyte, Priest and the AB skills;
    # renewal's transcendent one also inherits High Priest (Assumptio,
    # Basilica, Meditatio, Mana Recharge).
    TREE_FROM={"Arch_Bishop_T": "Arch_Bishop"},
    BASE="High_Priest",
    SKILL_PREFIX="AB_",
    HP_FROM="High_Priest", HP_SCALE=1.0,
    SP_FROM="High_Priest", SP_SCALE=1.0,
    EXP_FROM="High_Priest",
    # Renewal's Arch Bishop bonuses come to +43 by job 70; two more make +45.
    EXTRA_BONUS=[(68, "Int"), (70, "Dex")],
    EQUIP_JOBS=["Priest"],
    EQUIP_LABEL="High Priest or Arch Bishop",
    # Renewal prices the Arch Bishop's own skills for renewal's SP pools and
    # SP gear. On a High Priest's pool and without Meditatio or Mana
    # Recharge they sustained half a High Priest's healing in a party. The
    # party buffs now cost what a High Priest pays to give five people the
    # single buff; the heals give about a High Priest's Heal per SP
    # (Highness Heal) or more across a party (Coluceo Heal).
    SKILL_OVERRIDES={
        "AB_CLEMENTIA":    {"Requires.SpCost": [200, 228, 256]},
        "AB_CANTO":        {"Requires.SpCost": [160, 176, 192]},
        "AB_PRAEFATIO":    {"Requires.SpCost": [70, 78, 86, 94, 102, 109, 117, 125, 132, 140]},
        "AB_HIGHNESSHEAL": {"Requires.SpCost": [30, 43, 55, 68, 80]},
        "AB_CHEAL":        {"Requires.SpCost": [90, 100, 110]},
    },
    ITEMS_ABOUT="The Arch Bishop's weapons, from arch_bishop/equipment.csv.",
    CSV_DIR="arch_bishop",
)

rune_knight = ec.config(
    __file__, **COMMON,
    JOBS=("Rune_Knight_T",),
    # Renewal's Rune Knight tree: Novice, Swordman, Knight and the RK skills;
    # renewal's transcendent one also inherits Lord Knight (Aura Blade,
    # Berserk, Spiral Pierce, ...).
    TREE_FROM={"Rune_Knight_T": "Rune_Knight"},
    BASE="Lord_Knight",
    SKILL_PREFIX="RK_",
    HP_FROM="Lord_Knight", HP_SCALE=1.0,
    SP_FROM="Lord_Knight", SP_SCALE=1.0,
    EXP_FROM="Lord_Knight",
    # Renewal's Rune Knight bonuses come to +43 by job 70; two more make +45.
    EXTRA_BONUS=[(68, "Str"), (70, "Vit")],
    EQUIP_JOBS=["Knight"],
    EQUIP_LABEL="Lord Knight or Rune Knight",
    ITEMS_ABOUT="The Rune Knight's weapons, from rune_knight/equipment.csv.",
    CSV_DIR="rune_knight",
    # Rune stones. Pre-renewal's rune items have no reuse delay; renewal's
    # Crush Strike, Millennium Shield and Refresh runes have one, and get it
    # back. Giant Growth (STR +30, +250% on a Rune Knight's attacks, 30% of
    # hits 2.5x) lasts 15 minutes in renewal: here it is a burst, 30 seconds
    # once every 3 minutes, like Enchant Deadly Poison. Storm Blast hits
    # everything around for about 4400 a target; renewal lets a rune go
    # every second, about 2200 dmg/s a target from a stack of runes: here
    # one every 10 seconds, a burst well inside the area cap.
    ITEM_FIELDS={
        "Runstone_Rhydo": {"Delay": "renewal"},
        "Runstone_Verkana": {"Delay": "renewal"},
        "Runstone_Nosiege": {"Delay": "renewal"},
        "Runstone_Pertz": {"Delay": {"Duration": 10000, "Status": "Reuse_Stormblast"}},
        "Runstone_Turisus": {"Delay": {"Duration": 180000}},
    },
    SKILL_OVERRIDES={"RK_GIANTGROWTH": {"Duration1": 30000}},
    # What the rune stones' own descriptions do not say, or no longer get
    # right, after the delays above.
    ITEM_DESCRIPTIONS={
        "Runstone_Turisus": ["^FF0000Giant Growth lasts 30 seconds. The rune can be used again after 3 minutes.^000000"],
        "Runstone_Rhydo": ["^FF0000The rune can be used again after 30 seconds.^000000"],
        "Runstone_Verkana": ["^FF0000The rune can be used again after 60 seconds.^000000"],
        "Runstone_Nosiege": ["^FF0000The rune can be used again after 2 minutes.^000000"],
        "Runstone_Pertz": ["^FF0000The rune can be used again after 10 seconds.^000000"],
    },
)

royal_guard = ec.config(
    __file__, **COMMON,
    JOBS=("Royal_Guard_T",),
    # Renewal's Royal Guard tree: Novice, Swordman, Crusader and the LG
    # skills; renewal's transcendent one also inherits Paladin (Gloria
    # Domini, Martyr's Reckoning, Battle Chant, Rapid Smiting).
    TREE_FROM={"Royal_Guard_T": "Royal_Guard"},
    BASE="Paladin",
    SKILL_PREFIX="LG_",
    HP_FROM="Paladin", HP_SCALE=1.0,
    SP_FROM="Paladin", SP_SCALE=1.0,
    EXP_FROM="Paladin",
    # Renewal's Royal Guard bonuses come to +43 by job 70; two more make +45.
    EXTRA_BONUS=[(68, "Vit"), (70, "Str")],
    EQUIP_JOBS=["Crusader"],
    EQUIP_LABEL="Paladin or Royal Guard",
    ITEMS_ABOUT="The Royal Guard's weapons and shields, from royal_guard/equipment.csv.",
    CSV_DIR="royal_guard",
)

warlock = ec.config(
    __file__, **COMMON,
    JOBS=("Warlock_T",),
    # Renewal's Warlock tree: Novice, Mage, Wizard and the WL skills;
    # renewal's transcendent one also inherits High Wizard (Mystical
    # Amplification, Napalm Vulcan, Gravitation Field, ...).
    TREE_FROM={"Warlock_T": "Warlock"},
    BASE="High_Wizard",
    SKILL_PREFIX="WL_",
    HP_FROM="High_Wizard", HP_SCALE=1.0,
    SP_FROM="High_Wizard", SP_SCALE=1.0,
    EXP_FROM="High_Wizard",
    # Renewal's Warlock bonuses come to +43 by job 70; two more make +45.
    EXTRA_BONUS=[(68, "Int"), (70, "Dex")],
    EQUIP_JOBS=["Wizard"],
    EQUIP_LABEL="High Wizard or Warlock",
    ITEMS_ABOUT="The Warlock's weapons, from warlock/equipment.csv.",
    CSV_DIR="warlock",
    # Spellbooks. rAthena reads a book only renewal's way: a WL_MB_ book
    # casts Reading Spellbook (Reading), which needs the passive Reading
    # Spellbook. Pre-renewal has the active skill, neither of the others,
    # no such books and no spellbook_db rows, so all of it comes from
    # renewal. The books are sold in Geffen (npc/spellbook_seller.txt).
    NEW_SKILLS_FROM_RENEWAL=["WL_READING_SB_READING"],
    NEW_FROM_RENEWAL=["WL_MB_SG", "WL_MB_LOV", "WL_MB_MS", "WL_MB_DL", "WL_MB_JF",
                      "WL_MB_ES", "WL_MB_CR", "WL_MB_CL", "WL_MB_CM", "WL_MB_TV"],
    COPY_TABLES={"db/spellbook_db.yml": ("db/re/spellbook_db.yml", "READING_SPELLBOOK_DB", 1)},
    # Pre-renewal's Comet costs 2 Red Gemstones and renewal's none; an import
    # entry cannot take an item cost away, so pre-renewal's stays. Fitting for
    # the Warlock's biggest spell, and the README says so.
    ITEMCOST_KEPT=["WL_COMET"],
    # SP. Without Soul Drain (+20% max SP, SP back on single-target kills)
    # and at renewal's prices, the Warlock's area spells ran a full SP bar
    # dry three times faster than a High Wizard's amplified Meteor Storm at
    # the same damage, and Soul Expansion in about a minute. These costs
    # give its area spells about 0.8x the damage a High Wizard deals with a
    # full SP bar of amplified Meteor Storm, and its single-target spells about
    # 0.9x that of amplified Jupitel Thunder (README.md has the measurements).
    SKILL_OVERRIDES={
        "WL_CRIMSONROCK": {"Requires.SpCost": [25, 29, 34, 38, 42]},
        "WL_JACKFROST": {"Requires.SpCost": [22, 26, 30, 35, 39]},
        "WL_FROSTMISTY": {"Requires.SpCost": [26, 31, 37, 42, 47]},
        "WL_SOULEXPANSION": {"Requires.SpCost": [17, 20, 22, 25, 28]},
        "WL_HELLINFERNO": {"Requires.SpCost": [36, 39, 43, 46, 49]},
        # Chain Lightning strikes at least four times, all on a lone target:
        # scaled as single-target damage, its cost scaled with it.
        "WL_CHAINLIGHTNING": {"Requires.SpCost": [40, 45, 50, 55, 60]},
        "WL_TETRAVORTEX": {"Requires.SpCost": [108, 135, 162, 189, 216, 180, 216, 252, 288, 324]},
    },
)

# The expanded classes, reached by rebirth: a reborn Ninja becomes a Kagerou
# or Oboro, a reborn Gunslinger a Rebellion, a reborn Star Gladiator a Star
# Emperor, a reborn Soul Linker a Soul Reaper. Their NPCs and Lua are in the
# mod beside the third classes'; docs/mods/EXPANDED_CLASS_REBIRTH.md §1-§11.

kagerou_oboro = ec.config(
    __file__,
    MOD_NAME="transcendent-third-classes",
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
    # second, to everything around. A 3.5 s delay brings it to about half of
    # the Kagerou's single-target damage per target, the area rule the third
    # classes follow.
    SKILL_OVERRIDES={"KO_HAPPOKUNAI": {"AfterCastActDelay": "3500"}},
    # Pre-renewal has no fixed cast time and DEX shortens every cast to
    # nothing at 150; 75% of renewal's fixed cast becomes after-cast delay,
    # which DEX does not touch, and the rest is added to the cast time. Skills
    # with a 10 s+ cooldown keep it all as cast time (Izayoi halves it).
    FIXED_CAST_TO_DELAY=0.75,
    WEAPON_KINDS={
        "huuma":  dict(type="Weapon", sub="Huuma",  loc=["Both_Hand"],  label="Huuma Shuriken", unid="Huuma Shuriken"),
        "dagger": dict(type="Weapon", sub="Dagger", loc=["Right_Hand"], label="Dagger",         unid="Dagger"),
    },
    ITEMS_ABOUT="The Kagerou's and Oboro's gear, from kagerou_oboro/equipment.csv.",
    CSV_DIR="kagerou_oboro",
)

rebellion = ec.config(
    __file__,
    MOD_NAME="transcendent-third-classes",
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
    ITEMS_ABOUT="The Rebellion's gear, from rebellion/equipment.csv.",
    CSV_DIR="rebellion",
)

star_emperor = ec.config(
    __file__,
    MOD_NAME="transcendent-third-classes",
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
    ITEMS_ABOUT="The Star Emperor's gear, from star_emperor/equipment.csv.",
    CSV_DIR="star_emperor",
)

soul_reaper = ec.config(
    __file__,
    MOD_NAME="transcendent-third-classes",
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
    ITEMS_ABOUT="The Soul Reaper's gear, from soul_reaper/equipment.csv.",
    CSV_DIR="soul_reaper",
)

ec.run([guillotine_cross, shadow_chaser, arch_bishop, rune_knight, royal_guard, warlock,
        kagerou_oboro, rebellion, star_emperor, soul_reaper])
