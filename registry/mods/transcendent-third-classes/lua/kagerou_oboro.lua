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
-- A magical build casts the Ninja's spells; only their charm bonus is scaled,
-- below. registry/tools/transcendent-third-classes/balance-kagerou-oboro.json
-- has the runs for both builds.
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

-- Charms and the Ninja's spells. A Kagerou or Oboro holds up to ten charms
-- of one element for five minutes, and each adds to every ninjutsu of that
-- element (Ice Spear +20% a hit, Kamaitachi and Exploding Dragon +100%):
-- ten of them doubled the spells, as in renewal, which put a charged Oboro
-- at 1.8 times a High Wizard. The Ninja's spells are weak, so the charms
-- stay the Kagerou's and Oboro's real gain, but only part of their bonus
-- is kept: ten charms make Ice Spear about 1.6 times as strong. Without
-- charms a Kagerou or Oboro casts exactly as a Ninja does, never less.
--
-- The hook cannot count charms, so it takes the bonus as what the skill's
-- percentage holds above its pre-renewal formula for that level. Keeping
-- the rest of the spell intact matters against magic defence: soft MDEF
-- comes off every one of Ice Spear's twelve hits, so a spell scaled down
-- as a whole would lose far more on a warded monster than on the dummy.

local CHARM_KEPT = 48   -- percent of the charm bonus a Kagerou/Oboro keeps

local NINJUTSU_BASE = {   -- the stock percentage, by level (pre-renewal)
  NJ_HYOUSENSOU   = function(lv) return 100 end,            -- Ice Spear, water
  NJ_HYOUSYOURAKU = function(lv) return 100 + 50 * lv end,  -- Ice Meteor, water
  NJ_KAMAITACHI   = function(lv) return 100 + 100 * lv end, -- Kamaitachi, wind
  NJ_HUUJIN       = function(lv) return 100 end,            -- Wind Blade, wind
  NJ_RAIGEKISAI   = function(lv) return 160 + 40 * lv end,  -- Lightning Strike, wind
  NJ_BAKUENRYU    = function(lv) return 150 + 150 * lv end, -- Exploding Dragon, fire
  NJ_KOUENKA      = function(lv) return 90 end,             -- Fire Petal, fire
  NJ_KAENSIN      = function(lv) return 50 end,             -- Fire Formation, fire
}

local KAGEROU, OBORO = 4211, 4212

for name, base in pairs(NINJUTSU_BASE) do
  skill(name, {
    ratio = function(c, stock)
      local job = c.caster.job
      if job ~= KAGEROU and job ~= OBORO then return stock end
      local bonus = stock - base(c.skill_lv)
      if bonus <= 0 then return stock end
      return stock - bonus + bonus * CHARM_KEPT // 100
    end,
  })
end
