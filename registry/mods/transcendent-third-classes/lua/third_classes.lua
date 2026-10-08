-- transcendent-third-classes: third-class skill damage, at parity with the transcendent classes.
-- Percent of each skill's damage, measured against the transcendent class
-- with the same level, stats and weapon (README.md has the table):
--   Guillotine Cross vs Assassin Cross (Sonic Blow 1023 dmg/s): Cross Impact
--     937, Rolling Cutter + Cross Ripper Slasher 964; Venom Pressure from its
--     ratio, not measured.
--   Shadow Chaser vs Stalker (Double Strafe 2280): Triangle Shot 2243, Fatal
--     Menace 1076 a target, Feint Bomb about 2200 a blast every 5 s.
--   Arch Bishop vs High Wizard (Cold Bolt 847): Adoramus 636, Judex 564,
--     Duple Light's magic strikes about 490 with auto-attacks. Its heals are
--     balanced by SP cost instead (build.py, SKILL_OVERRIDES).
--   Rune Knight vs Lord Knight (Spiral Pierce 1562): Sonic Wave 1415, Hundred
--     Spear 1450; per target Wind Cutter 1222, Ignition Break 1198, Dragon
--     Breath 991 (more with HP). Giant Growth is limited in build.py.
--   Royal Guard vs Paladin (Rapid Smiting 1903): Banishing Point 1747; per
--     target Overbrand 1013, Earth Drive 943, Cannon Spear 935.
local FACTOR = {
  GC_CROSSIMPACT        = 29,
  GC_ROLLINGCUTTER      = 30,
  GC_CROSSRIPPERSLASHER = 8,
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
  RK_WINDCUTTER         = 8,
  RK_IGNITIONBREAK      = 66,
  RK_DRAGONBREATH       = 85,
  RK_DRAGONBREATH_WATER = 85,
  LG_BANISHINGPOINT     = 25,
  LG_OVERBRAND          = 11,
  LG_CANNONSPEAR        = 70,
  LG_EARTHDRIVE         = 70,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
