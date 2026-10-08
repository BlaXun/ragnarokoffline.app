-- rebellion: Rebellion skill damage, scaled for pre-renewal.
--
-- rAthena's RL_ skill classes carry renewal's formulas. On a pre-renewal
-- server they land far above the transcendent classes: Fire Dance did 3.5
-- times a Sniper's Double Strafe per second, to everything around, and one
-- Slug Shot hit for 45,000.
--
-- Each factor scales the skill's own percentage, after everything the server
-- adds to it (Desperado's bonus to Fire Dance, coins), so those keep their
-- share. The aim is a little below a transcendent class. Measured on a
-- pre-renewal server, damage per second over 30 s against one DEF 30 / VIT 30
-- target, all characters base 99 with the same DEX build and a 150 ATK weapon
-- of their kind:
--
--   Single target, skills of one gun used together      Rebellion   Sniper
--     Rifle: Mass Spiral + Anti-Material Blast              2085    2454 Double Strafe
--     Shotgun: Banishing Buster + Slug Shot + Shatter Storm 2209
--   Area
--     Fire Dance (revolver)                                 1036     814 Sharp Shooting
--     Round Trip, Fire Rain (gatling)                       1003
--     Shatter Storm (shotgun)                               1010
--
-- The area skills sit at 0.85 of the best transcendent area skill measured
-- (Meteor Assault, 1180), which is above the Sniper's own Sharp Shooting.
--
-- Skills of one gun are scaled together, since their cooldowns interleave:
-- Mass Spiral alone at 90% already matched the target, and with Anti-Material
-- Blast between its casts the pair did 1.8 times it.
--
-- Left as they are: Howling Mine (910), Hammer of God (a finisher that spends
-- every coin), Quick Draw Shot (a Chain Action proc), and the buffs and traps.
-- Dragon Tail spends its missile and deals no damage on the pinned rAthena,
-- with or without a Crimson Marker: that is in the server, not in this file.

local FACTOR = {
  RL_MASS_SPIRAL      = 45,
  RL_AM_BLAST         = 30,
  RL_BANISHING_BUSTER = 23,
  RL_SLUGSHOT         = 17,
  RL_FIREDANCE        = 12,
  RL_R_TRIP           = 31,
  RL_FIRE_RAIN        = 40,
  RL_S_STORM          = 28,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
