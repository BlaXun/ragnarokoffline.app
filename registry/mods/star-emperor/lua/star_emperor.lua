-- star-emperor: Star Emperor skill damage, scaled for pre-renewal.
--
-- rAthena's SJ_ skill classes carry renewal's formulas. On a pre-renewal
-- server they land far above the transcendent classes: Prominence Kick did
-- 2.9 times an Assassin Cross's Sonic Blow per second, the New/Full Moon Kick
-- pair 2.9 times his Meteor Assault, and Falling Star turned plain attacks
-- into 1.8 times Sonic Blow.
--
-- Each factor scales the skill's own percentage, after everything the server
-- adds to it. The aim is a little below a transcendent class. Measured on a
-- pre-renewal server, damage per second over 30 s against one DEF 30 / VIT 30
-- target, both characters base 99 with the same STR build and a 150 ATK
-- weapon (a book for the Star Emperor, in Universe Stance):
--
--                                               Star Emperor  Assassin Cross
--   Prominence Kick (+ Solar Burst)                   886     1022 Sonic Blow
--   Attacks with Falling Star, targets Flash-Kicked   858     1022
--   New Moon Kick + Full Moon Kick (area)             990     1180 Meteor Assault
--
-- Falling Star's two extra hits are scaled at 40%: the second follows the
-- first, so the pair falls faster than the factor.
--
-- Left as they are: Flash Kick (a marker, 333/s on its own), the stances and
-- Lights (buffs), and the skills rAthena allows only on PvP and GvG maps
-- (Nova Explosion, Star Emperor Advent, Gravity Control, the two Books),
-- which this measurement could not reach.

local FACTOR = {
  SJ_PROMINENCEKICK   = 30,
  SJ_SOLARBURST       = 30,
  SJ_NEWMOONKICK      = 29,
  SJ_FULLMOONKICK     = 29,
  SJ_FALLINGSTAR_ATK  = 40,
  SJ_FALLINGSTAR_ATK2 = 40,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
