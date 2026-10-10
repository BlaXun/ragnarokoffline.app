-- transcendent-third-classes: third-class skill damage, at parity with the transcendent classes.
-- Percent of each skill's damage, measured against the transcendent class
-- with the same level, stats and weapon (README.md has the table; to re-measure,
-- registry/tools/transcendent-third-classes/balance.json). A
-- fighting class's area attacks deal about half its best single target to
-- each target; the Warlock, a caster whose job area damage is, is exempt:
--   Guillotine Cross vs Assassin Cross (Sonic Blow 1010 dmg/s): Cross Impact
--     925, Rolling Cutter + Cross Ripper Slasher 950, Rolling Cutter alone 468
--     a target; Venom Pressure from its ratio, not measured.
--   Shadow Chaser vs Stalker (Double Strafe 2280): Triangle Shot 2243, Fatal
--     Menace 1076 a target, Feint Bomb about 2200 a blast every 5 s.
--   Arch Bishop vs High Wizard (Mystical Amplification + Meteor Storm 1255-
--     1588 a target): Adoramus 658 and Judex 656 a target, about half, as a
--     support caster's; Duple Light's magic strikes about 490 with auto-attacks. Its heals are
--     balanced by SP cost instead (build.py, SKILL_OVERRIDES).
--   Rune Knight vs Lord Knight (Spiral Pierce 1562): Sonic Wave 1497, Hundred
--     Spear 1450; per target Wind Cutter 817, Ignition Break 711, Dragon
--     Breath 743 (more with HP). Giant Growth is limited in build.py.
--   Royal Guard vs Paladin (Rapid Smiting 1876): Banishing Point 1729; per
--     target Overbrand 826, Earth Drive 864, Cannon Spear 871.
--   Warlock vs High Wizard (Mystical Amplification + Jupitel 2008-2288, +
--     Meteor Storm 1348-1396 a target): Hell Inferno 1745, Tetra Vortex 1909,
--     Soul Expansion 1904, Chain Lightning 1886 (all four strikes on a lone
--     target); a target Jack Frost 1512, Crimson Rock 1363, Frost Misty 1411,
--     Comet 1409. SP costs: build.py.
--   Sorcerer vs High Wizard (as the Warlock; Mystical Amplification and
--     Jupitel about 2080, and Meteor Storm about 1440 a target): Varetyr
--     Spear about 1890, Spell Fist about 2110 (below); per target Psychic
--     Wave 1456, Poison Buster 1556, Cloud Kill 1648, a caster's area at
--     parity.
local FACTOR = {
  GC_CROSSIMPACT        = 29,
  GC_ROLLINGCUTTER      = 20,
  GC_CROSSRIPPERSLASHER = 9,
  GC_COUNTERSLASH       = 30,
  GC_VENOMPRESSURE      = 40,
  SC_TRIANGLESHOT       = 15,
  SC_FATALMENACE        = 10,
  SC_FEINTBOMB          = 25,
  AB_ADORAMUS           = 17,
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
  WL_HELLINFERNO        = 30,
  WL_TETRAVORTEX_FIRE   = 40,
  WL_TETRAVORTEX_WATER  = 40,
  WL_TETRAVORTEX_WIND   = 40,
  WL_TETRAVORTEX_GROUND = 40,
  WL_CRIMSONROCK        = 47,
  WL_JACKFROST          = 61,
  WL_FROSTMISTY         = 62,
  WL_CHAINLIGHTNING_ATK = 36,
  WL_COMET              = 85,
  SO_PSYCHIC_WAVE       = 29,
  SO_POISON_BUSTER      = 47,
  SO_CLOUD_KILL         = 38,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end

-- Spell Fist (Sorcerer): cast while a bolt is being cast, it cancels the
-- bolt and turns every auto-attack after it into that bolt's magic damage,
-- for 20 SP a hit, until the SP or the three minutes run out. In renewal
-- that was about 7,300 a second here, three times a High Wizard's
-- amplified Jupitel Thunder. The hit is computed through the bolt's own
-- skill, so the bolt is scaled only for a Sorcerer under Spell Fist; a
-- Wizard's or a Sorcerer's ordinary bolt is untouched.
local SORCERER_T = 4074
local SPELLFIST_KEPT = 26   -- percent of the bolt a Spell Fist hit keeps

for _, name in ipairs({ "MG_FIREBOLT", "MG_COLDBOLT", "MG_LIGHTNINGBOLT", "WZ_EARTHSPIKE" }) do
  skill(name, {
    ratio = function(c, stock)
      if c.caster.job == SORCERER_T and c.caster:has_status("SC_SPELLFIST") then
        return stock * SPELLFIST_KEPT // 100
      end
      return stock
    end,
  })
end
