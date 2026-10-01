-- Thorns Plate: reflects 15% of physical damage back on the attacker.
--
-- The filter is one line: `if c.weapon_type ~= "weapon" then return end`.
-- Any magical or misc attack falls out of the hook before anything else
-- happens, so mages and misc-damage traps hit through the armor at full
-- power -- which is the thing about this armor you want to be true.
--
-- Physical skills (Bash, Double Strafe, Mammonite, ...) count as weapon
-- attacks too, so the thorns fire for both normal attacks and physical
-- skill hits.

item("Thorns_Plate", {
  priority = 5,

  on_hit_taken = function(c)
    -- Only physical attacks. The server tags each hit as
    -- "weapon" (BF_WEAPON), "magic" (BF_MAGIC) or "misc" (BF_MISC).
    if c.weapon_type ~= "weapon" then
      return
    end

    -- Only on hits that connected and did non-trivial damage. A grazing
    -- attack for 1 damage is not worth reflecting.
    if not c.connected or c.damage < 10 then
      return
    end

    -- Reflect 15% back as HP damage on the attacker. c:status with the
    -- bleeding status is a clean way to deliver damage over time without
    -- having to touch unit HP directly -- SC_BLEEDING ticks for the
    -- attacker's base MaxHP percentage.
    --
    -- Short duration (3s), high rate (100% out of 10000), and routed to
    -- the caster (the attacker), not us.
    c:status("SC_BLEEDING", 10000, 3000, 1, "caster")
    log("Thorns Plate: reflected onto", c.caster.name,
        "(" .. c.damage .. " dmg,", c.weapon_type .. ")")
  end,
})
