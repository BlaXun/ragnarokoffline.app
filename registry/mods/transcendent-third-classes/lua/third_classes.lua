-- transcendent-third-classes: third-class skill damage, at parity with the transcendent classes.
-- Percent of each skill's damage, measured against the transcendent class
-- with the same level, stats and weapon (README.md has the table):
--   Guillotine Cross vs Assassin Cross (Sonic Blow 1023 dmg/s): Cross Impact
--     937, Rolling Cutter + Cross Ripper Slasher 964; Venom Pressure from its
--     ratio, not measured.
--   Shadow Chaser vs Stalker (Double Strafe 2280): Triangle Shot 2243, Fatal
--     Menace 1076 a target, Feint Bomb about 2200 a blast every 5 s.
local FACTOR = {
  GC_CROSSIMPACT        = 29,
  GC_ROLLINGCUTTER      = 30,
  GC_CROSSRIPPERSLASHER = 8,
  GC_COUNTERSLASH       = 30,
  GC_VENOMPRESSURE      = 40,
  SC_TRIANGLESHOT       = 15,
  SC_FATALMENACE        = 10,
  SC_FEINTBOMB          = 25,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
