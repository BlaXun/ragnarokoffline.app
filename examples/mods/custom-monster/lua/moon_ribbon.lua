-- Moon Ribbon: when you are hit below 30% HP, a 20% chance to cast Heal Lv 5
-- on yourself.
--
-- An item script can say "3% chance to cast Heal when hit"
-- (bonus3 bAutoSpellWhenHit), but not "only when it's needed". A Lua item
-- hook can: it runs for whoever has the item equipped, each time they are
-- hit, and c:cast() casts the way the autospell bonuses do.
item("Moon_Ribbon", {
  on_hit_taken = function(c)
    local low = c.caster.hp * 100 < c.caster.maxhp * 30
    if low and c:chance(2000) then
      c:cast("AL_HEAL", 5, "caster")
    end
  end,
})
