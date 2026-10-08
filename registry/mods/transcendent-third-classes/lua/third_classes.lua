-- transcendent-third-classes: third-class skill damage, at parity with the transcendent classes.
local FACTOR = {
  GC_CROSSIMPACT        = 29,
  GC_ROLLINGCUTTER      = 30,
  GC_CROSSRIPPERSLASHER = 8,
  GC_COUNTERSLASH       = 30,
  GC_VENOMPRESSURE      = 40,
}

for name, percent in pairs(FACTOR) do
  skill(name, {
    ratio = function(c, stock)
      return stock * percent // 100
    end,
  })
end
