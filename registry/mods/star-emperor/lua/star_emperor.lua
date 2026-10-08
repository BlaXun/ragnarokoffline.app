-- star-emperor: Star Emperor skill damage, scaled for pre-renewal.
--
-- rAthena's SJ_ skill classes carry renewal's formulas. On a pre-renewal
-- server they land far above the transcendent classes: Prominence Kick did
-- 2.9 times an Assassin Cross's Sonic Blow per second, the New/Full Moon Kick
-- pair 2.9 times his Meteor Assault, and Falling Star turned plain attacks
-- into 1.8 times Sonic Blow.
--
-- db/skill_db.yml also turns 75% of each renewal fixed cast into after-cast
-- delay and the rest into cast time, since pre-renewal has no fixed cast and
-- DEX would shorten New Moon Kick and the others to nothing (see build.py).
--
-- Each factor scales the skill's own percentage, after everything the server
-- adds to it. The aim is a little below a transcendent class. Measured on a
-- pre-renewal server, damage per second over 45 s against one DEF 30 / VIT 30
-- target, both characters base 99 with the same STR build and a 150 ATK
-- weapon (a book for the Star Emperor, in Universe Stance):
--
--                                               Star Emperor  Assassin Cross
--   Prominence Kick (+ Solar Burst)                   922     1044 Sonic Blow
--   Attacks with Falling Star, targets Flash-Kicked   904     1044
--   New Moon Kick + Full Moon Kick (area)             954     1180 Meteor Assault
--
-- Universe Stance is a toggle and Falling Star lasts minutes: both were cast
-- once at the start. (An earlier measurement recast the stance every 10 s,
-- which switched it off half the time and undercounted every kick.)

local FACTOR = {
  SJ_PROMINENCEKICK   = 21,
  SJ_SOLARBURST       = 21,
  SJ_NEWMOONKICK      = 22,
  SJ_FULLMOONKICK     = 22,
  SJ_FALLINGSTAR_ATK  = 26,
  SJ_FALLINGSTAR_ATK2 = 26,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
