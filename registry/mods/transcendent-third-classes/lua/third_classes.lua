-- transcendent-third-classes: third-class skill damage, at parity with the transcendent classes.
-- Percent of each skill's damage, measured against the transcendent class
-- with the same level, stats and weapon (README.md has the table). A
-- fighting class's area attacks deal about half its best single target to
-- each target; the Warlock, a caster whose job area damage is, is exempt:
--   Guillotine Cross vs Assassin Cross (Sonic Blow 1010 dmg/s): Cross Impact
--     925, Rolling Cutter + Cross Ripper Slasher 950, Rolling Cutter alone 468
--     a target; Venom Pressure from its ratio, not measured.
--   Shadow Chaser vs Stalker (Double Strafe 2280): Triangle Shot 2243, Fatal
--     Menace 1076 a target, Feint Bomb about 2200 a blast every 5 s.
--   Arch Bishop vs High Wizard (Mystical Amplification + Meteor Storm 1255-
--     1588 a target): Adoramus 614 and Judex 722 a target, about half, as a
--     support caster's; Duple Light's magic strikes about 490 with auto-attacks. Its heals are
--     balanced by SP cost instead (build.py, SKILL_OVERRIDES).
--   Rune Knight vs Lord Knight (Spiral Pierce 1562): Sonic Wave 1497, Hundred
--     Spear 1450; per target Wind Cutter 817, Ignition Break 711, Dragon
--     Breath 743 (more with HP). Giant Growth is limited in build.py.
--   Royal Guard vs Paladin (Rapid Smiting 1876): Banishing Point 1729; per
--     target Overbrand 826, Earth Drive 864, Cannon Spear 871.
--   Warlock vs High Wizard (Mystical Amplification + Jupitel 2032, + Meteor
--     Storm 1255 a target): Hell Inferno 1926, Tetra Vortex 1995, Soul
--     Expansion 1836; a target Jack Frost 1390, Crimson Rock 1280, Chain
--     Lightning 1259, Frost Misty 1249, Comet 1409. SP costs: build.py.
local FACTOR = {
  GC_CROSSIMPACT        = 29,
  GC_ROLLINGCUTTER      = 20,
  GC_CROSSRIPPERSLASHER = 9,
  GC_COUNTERSLASH       = 30,
  GC_VENOMPRESSURE      = 40,
  SC_TRIANGLESHOT       = 15,
  SC_FATALMENACE        = 10,
  SC_FEINTBOMB          = 25,
  AB_ADORAMUS           = 15,
  AB_JUDEX              = 25,
  AB_DUPLELIGHT_MAGIC   = 50,
  RK_SONICWAVE          = 17,
  RK_HUNDREDSPEAR       = 76,
  RK_WINDCUTTER         = 5,
  RK_IGNITIONBREAK      = 40,
  RK_DRAGONBREATH       = 64,
  RK_DRAGONBREATH_WATER = 64,
  LG_BANISHINGPOINT     = 25,
  LG_OVERBRAND          = 9,
  LG_CANNONSPEAR        = 64,
  LG_EARTHDRIVE         = 66,
  WL_HELLINFERNO        = 48,
  WL_TETRAVORTEX_FIRE   = 40,
  WL_TETRAVORTEX_WATER  = 40,
  WL_TETRAVORTEX_WIND   = 40,
  WL_TETRAVORTEX_GROUND = 40,
  WL_CRIMSONROCK        = 47,
  WL_JACKFROST          = 61,
  WL_FROSTMISTY         = 56,
  WL_CHAINLIGHTNING_ATK = 72,
  WL_COMET              = 85,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
