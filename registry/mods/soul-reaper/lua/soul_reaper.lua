-- soul-reaper: Soul Reaper skill damage, scaled for pre-renewal.
--
-- rAthena's SP_ skill classes carry renewal's formulas, and pre-renewal has no
-- fixed cast time. db/skill_db.yml turns 75% of each renewal fixed cast into
-- after-cast delay and the rest into cast time (see build.py); before that,
-- Espa cast in a quarter of a second and did 30 times a High Wizard's damage
-- per second. After it, Espa still did 11 times.
--
-- Each factor scales the skill's own percentage, after everything the server
-- adds to it. The aim is 0.85-1.0 of a transcendent class. Measured on a
-- pre-renewal server, damage per second over 40 s against one MDEF 10 target
-- that neither hits back nor moves, both characters base 99 with the same
-- INT/DEX build and a +15% MATK staff:
--
--                                           Soul Reaper   High Wizard
--   Espa (costs no soul energy at Lv 10)       1587       1829 Jupitel Thunder
--   Espa + Eswhoo, soul energy unlimited        1567        986 Cold Bolt
--   Soul Curse + Curse Explosion, unlimited    ~5900
--
-- The runs behind these are in registry/tools/soul-reaper/balance.json.
--
-- The first measurement put the High Wizard at about 850: the test dummy hit
-- back and every hit interrupted a cast, and a repeated request restarted
-- one. The Soul Reaper's Espa measured right then (734); Jupitel Thunder and
-- Curse Explosion, with long casts, did not. Espa and Eswhoo were raised, and
-- Eswhoo again so that spending soul energy on it pays (it had measured below
-- Espa alone).
--
-- Against monsters soul energy comes only from Soul Collect (one every 20 s
-- at Lv 5): the Soul Reaper buff gains it only from hitting players. So Espa
-- carries the damage and Eswhoo and Curse Explosion are its occasional
-- bursts; even with energy to spare, they do not raise the rate.
--
-- Left as they are: Esha (a debuff, 25/s of damage), the soul links and
-- buffs, and Soul Division and Soul Explosion, which rAthena allows only on
-- PvP and GvG maps.

local FACTOR = {
  SP_SPA            = 15,
  SP_SWHOO          = 21,
  SP_CURSEEXPLOSION = 50,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
