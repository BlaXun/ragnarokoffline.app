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
-- The aim is 0.85-1.0 of a transcendent class on one target, and about half of
-- the Kagerou's own single target on each target of an area (the third
-- classes' area rule). Measured on a pre-renewal server, damage per second
-- over 40 s against one DEF 30 / VIT 30 target, both characters base 99 with
-- the same stats and a 150 ATK weapon of their kind:
--
--                                          Kagerou   Assassin Cross
--   Cross Slash Lv 10 + Soul Cutter Lv 5      872    1016  Sonic Blow Lv 10
--   Swirling Petal Lv 10 (area, a target)     440
--   Kunai Splash Lv 5 (area, a target)        488
--   Kunai Explosion Lv 5 (area, a target)     430
--
-- The Ninja's spells (a magical build) are not scaled; registry/tools/
-- kagerou-oboro/balance.json has those runs too.
--
-- Cross Slash was measured with a dagger in each hand, on a target carrying
-- its own Cross Wound (754 per cast without the wound, about 2,100 with it:
-- rAthena lets a Kagerou's own wound count, not only a partner's). It has a
-- 3.1 s cooldown. Kunai Splash's damage is added outside the
-- percentage, so a factor here cannot reach it: db/skill_db.yml gives it a
-- 3.5 s delay instead. Rapid Throw (zeny), Illusion - Death (% of HP) and the
-- Oboro skills (buffs and debuffs) are left as they are.

local FACTOR = {
  KO_JYUMONJIKIRI = 20,  -- Cross Slash
  KO_SETSUDAN     = 70,  -- Soul Cutter
  KO_HUUMARANKA   = 40,  -- Swirling Petal
  KO_BAKURETSU    = 53,  -- Kunai Explosion
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
