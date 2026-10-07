-- kagerou-oboro: Kagerou and Oboro skill damage, scaled for pre-renewal.
--
-- rAthena's KO_ skill classes carry renewal's formulas, which were written for
-- base level 175 and renewal's damage pipeline. On a pre-renewal server they
-- land well away from the transcendent classes: Cross Slash and Soul Cutter
-- together did 1.6 times an Assassin Cross's Sonic Blow, while Swirling Petal
-- did a third of his Meteor Assault.
--
-- Each factor scales the skill's own percentage, after everything the server
-- adds to it (the Cross Slash mark, Kagemusya), so those keep their share.
-- The aim is a little below a transcendent class. Measured on a pre-renewal
-- server, damage per second over 30 s against one DEF 30 / VIT 30 target, both
-- characters base 99 with the same stats and a 150 ATK weapon of their kind:
--
--                                          Kagerou   Assassin Cross
--   Cross Slash Lv 10 + Soul Cutter Lv 5      875    1020  Sonic Blow Lv 10
--   Swirling Petal Lv 10 (area)               975    1180  Meteor Assault Lv 10
--   Kunai Splash Lv 5 (area)                  813    1180
--   Kunai Explosion Lv 5 (area, ranged)       830    1180
--
-- One Cross Slash hits as hard as one Sonic Blow, but it has a 3.1 s cooldown
-- and needs a weapon in each hand. Kunai Splash's damage is added outside the
-- percentage, so a factor here cannot reach it: db/skill_db.yml gives it a 2 s
-- delay instead. Kunai Explosion, Rapid Throw (zeny), Illusion - Death (% of
-- HP) and the Oboro skills (buffs and debuffs) are left as they are.

local FACTOR = {
  KO_JYUMONJIKIRI = 20,  -- Cross Slash
  KO_SETSUDAN     = 70,  -- Soul Cutter
  KO_HUUMARANKA   = 85,  -- Swirling Petal
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
