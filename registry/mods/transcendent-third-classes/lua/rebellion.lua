-- rebellion: Rebellion skill damage, scaled for pre-renewal.
--
-- rAthena's RL_ skill classes carry renewal's formulas. On a pre-renewal
-- server they land far above the transcendent classes: Fire Dance did 3.5
-- times a Sniper's Double Strafe per second, to everything around, and one
-- Slug Shot hit for 45,000.
--
-- db/skill_db.yml also turns 75% of each renewal fixed cast into after-cast
-- delay and the rest into cast time, since pre-renewal has no fixed cast and
-- DEX would shorten Mass Spiral and the other gun skills to nothing (see
-- build.py). The factors below were measured after that.
--
-- Each factor scales the skill's own percentage, after everything the server
-- adds to it (Desperado's bonus to Fire Dance, coins), so those keep their
-- share. The aim is 0.85-1.0 of a transcendent class. Measured on a
-- pre-renewal server, damage per second over 30 s against one DEF 30 / VIT 30
-- target, all characters base 99 with the same DEX build and a 150 ATK weapon
-- of their kind:
--
--   Single target, skills of one gun used together      Rebellion   Sniper
--     Rifle: Mass Spiral + Anti-Material Blast              2309    2448 Double Strafe
--     Shotgun: Banishing Buster + Slug Shot + Shatter Storm 2203
--     Grenade: Howling Mine + Dragon Tail, target marked    2105
--   Area
--     Fire Dance (revolver)                                 1042     814 Sharp Shooting
--     Round Trip, Fire Rain (gatling)                 1088, 1011
--     Shatter Storm (shotgun)                                999
--
-- The runs behind these are in registry/tools/transcendent-third-classes/balance-rebellion.json.
--
-- Each gun aims at 0.85-1.0 of the Sniper on one target, and the area skills
-- at about half of the rifle on each target (0.43-0.47), the third classes'
-- area rule; at a Sniper's scale that is still above Sharp Shooting.
--
-- Skills of one gun are scaled together, since their cooldowns interleave:
-- Mass Spiral alone at 90% already matched the target, and with Anti-Material
-- Blast between its casts the pair did 1.8 times it.
--
-- Dragon Tail is scaled alone in its pair: Howling Mine on its own does 910
-- and is left as it is, as are Hammer of God (a finisher that spends every
-- coin), Quick Draw Shot (a Chain Action proc), and the buffs and traps.

local FACTOR = {
  RL_MASS_SPIRAL      = 72,
  RL_AM_BLAST         = 48,
  RL_BANISHING_BUSTER = 31,
  RL_SLUGSHOT         = 23,
  RL_FIREDANCE        = 12,
  RL_R_TRIP           = 31,
  RL_FIRE_RAIN        = 40,
  RL_S_STORM          = 30,
  RL_D_TAIL           = 33,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
