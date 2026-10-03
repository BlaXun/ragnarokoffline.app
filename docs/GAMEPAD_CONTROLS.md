# Playing with a gamepad

The client plays with a controller out of the box: plug one in (or pair it) and
press any button. Nothing needs installing, and no mod is involved — gamepad
support is part of the roBrowser client this app ships, extended in our fork.

Any controller the browser reports with the *standard* layout works: Xbox,
PlayStation and most others. This page uses Xbox names:

| Xbox | PlayStation |
|---|---|
| `A` `B` `X` `Y` | `✕` `○` `□` `△` |
| `LB` `RB` | `L1` `R1` |
| `LT` `RT` | `L2` `R2` |
| `View` | `Share` / `Create` |
| `Menu` | `Options` |
| `LS click` / `RS click` | `L3` / `R3` |

A small overlay — the **gamepad HUD** — appears on the first input. It shows the shortcut groups and which set is active, lights
up the group you are holding, and hides itself after thirty seconds without
input.

---

## At a glance

| Control | Does |
|---|---|
| Left stick | walk |
| Right stick | move the cursor |
| `A` | click at the cursor |
| `B` | right click at the cursor; hold on an item or skill to put it on a shortcut |
| `X` | attack the selected monster, or the nearest one |
| `Y` | pick up the selected item, or the nearest one |
| D-pad `◀` `▶` | select the previous / next target |
| D-pad `▲` `▼` | up / down in lists and item grids |
| `LS click` | switch what the D-pad selects: monsters, items, or both |
| `RS click` | clear the target and recentre the cursor |
| `Menu` | enter |
| `View` + D-pad `▲` `▼` | zoom in / out |
| `View` + D-pad `◀` `▶` | turn the camera |
| `View` + `Menu` | escape |
| `View` (cursor on an item or skill) | its context menu |
| hold `LB` `RB` `LT` or `RT` + `Y` `X` `B` `A` | use a shortcut — see below |
| hold `LT` + `RT` | switch shortcut set |

Every button can be moved to another — see *Remapping*.

---

## Walking and the camera

**Push the left stick at least halfway to walk.** Ragnarok has no directional
walk, only *walk to this cell*, so a held stick becomes a destination a few
cells ahead, renewed while you hold it. A light push does nothing on purpose:
a stick on its way back to the centre would otherwise send one last short step,
or turn you on the spot.

The direction follows the camera, so **up is up the screen**, not up the map,
at any camera angle.

Letting go stops new steps being sent. Your character may finish the few cells
the server already accepted; there is no instant stop in the protocol.

`View` + D-pad turns and zooms the camera. Indoor maps limit how far the camera
turns, exactly as they do for the mouse.

## Fighting

### Picking a target

**D-pad `◀` `▶` steps through nearby monsters**, nearest first, and wraps
round at the ends. The selected one gets the lock-on arrow, and the cursor
jumps onto it.

**`LS click` changes what the D-pad steps through** — monsters, ground items, or
both mixed by distance. The chat box names the new mode. The same choice is
**D-pad Cycle Targets** in the settings.

Selecting is only selecting: it never attacks, and stepping to the next monster
mid-fight does not stop the one you are hitting.

**`RS click` clears the selection** and puts the cursor back in the middle of
the screen.

### Attacking

**`X` attacks the selected monster.** With nothing selected it picks one itself
— the nearest, or the weakest if **Attack Target Mode** is set to *Lowest HP*.
If the monster is out of reach your character walks to it first.

It sends Ragnarok's *continuous* attack, so **the server keeps swinging until
the target falls.** Hold `X` and, when that one dies, you move on to the next
target by yourself; a fresh press always attacks again.

After `X` the left stick is ignored until it returns to the centre, so you can
push towards a monster, press `X` and let go without cancelling the walk to it.
Push the stick again to walk away — that ends the attack, as clicking the ground
would.

### Skills on a target

A skill that needs a target puts the client into target selection, as with the
mouse. **Quick-Cast Mode** decides what happens next:

| Quick-Cast Mode | After pressing the shortcut |
|---|---|
| **Off** | aim with the right stick and press `A` |
| **Release Mode** | aim while you hold the shortcut; it casts at the cursor when you let go |
| **Instant Mode** | casts at once — on the selected monster if there is one, wherever it has walked, otherwise at the cursor. Ground skills land where the selected monster stands |

Items and self skills never trigger a quick-cast click, so drinking a potion
mid-fight does not interrupt your attack.

**Heal goes to a selected monster.** The game counts it as usable on enemies
(it damages undead), so with a monster selected, Instant Mode casts it there.
Clear the selection with `RS click` to heal yourself.

### Picking things up

**`Y` picks up the selected item**, or the nearest one when none is selected,
walking to it first if it is more than two cells away. To pick a particular item
out of a pile, switch the D-pad to items with `LS click` and step to it.

---

## Skills and items — shortcut groups

Gamepad shortcuts use the same shortcut bar as the keyboard (see
[KEYBOARD_CONTROLS.md](KEYBOARD_CONTROLS.md)). **Hold a shoulder button, then
press a face button**; `Y` `X` `B` `A` are slots 1–4 of that group:

| Hold | `Y` `X` `B` `A` use | In set 2 |
|---|---|---|
| `LB` | bar 1, slots 1–4 | bar 3, slots 1–4 |
| `LT` | bar 1, slots 5–8 | bar 3, slots 5–8 |
| `RB` | bar 2, slots 1–4 | bar 4, slots 1–4 |
| `RT` | bar 2, slots 5–8 | bar 4, slots 5–8 |
| `LB` + `RB` | slot 9 of bar 1 / 2 / 3 / 4 | the same |

Bar 1 is the `F1`–`F9` row, bar 2 the `1`–`9` row, bars 3 and 4 the `Q` and
`A` rows. **Hold `LT` + `RT` together to switch between set 1 and set 2**; the
HUD shows which is active.

**Putting something on a shortcut without the mouse:** open the inventory or
skill window, move the cursor onto the item or skill, and **hold `B`**. A
*Select slot* window opens: `LT` / `RT` change the bar, the D-pad picks the
slot, `A` places it and `View` cancels. Etc. items, cards, pet eggs and pet
armour cannot go on a shortcut this way.

## The cursor and windows

The right stick moves the cursor. A slight push moves it slowly for precise
aiming — picking a small item off the ground, say — and full tilt moves it
quickly; **Mouse Move Sensitivity** sets the top speed.

`A` and `B` click wherever the cursor is, in windows as well as on the map.
With the cursor on an item or skill grid, the D-pad moves from cell to cell.
`Menu` is enter and `View` + `Menu` is escape, which also opens the game menu.

---

## Settings

Press escape (`View` + `Menu`), open the **shortcut settings** from the menu,
and choose the **Gamepad** tab. Changes apply at once and are saved per
browser.

| Setting | Does |
|---|---|
| **Button Mapping** | opens the mapping panel — see *Remapping* |
| **Attack Target Mode** | how `X` picks a target when none is selected: *Off* or *Closest* the nearest, *Lowest HP* the weakest. Any setting but *Off* also points targeted shortcut skills at that target |
| **D-pad Cycle Targets** | monsters, items or both (also `LS click`) |
| **Quick-Cast Mode** | Off / Release / Instant — see *Skills on a target* |
| **Mouse Move** | cursor speed at full tilt |
| **Disable Virtual Mouse** | `A` and `B` stop clicking at the cursor (`B` still right-clicks the map); play with `X`, `Y`, the D-pad and shortcuts |
| **Swap L3-R3 Sticks** | walk with the right stick, move the cursor with the left |
| **Auto Hide UI** | hide the gamepad HUD as soon as the real mouse moves |
| **Axis Threshold** | the sticks' deadzone, for controllers that drift |

## Remapping

**Button Mapping → Mapping** lists every job a button does, the button doing it
now, and a **Remap** button. Press **Remap**, then the button you want on the
controller. The two buttons **trade places**: give *Attack* to `Y` and *Pick
up* moves to `X`. Nothing can end up unassigned or on two buttons, and the
combinations follow — after that swap, `LB` + `X` uses what `LB` + `Y` used to.

Press **Remap** again to cancel. **Reset to defaults** puts every button back.
The HUD's labels follow your mapping.

The `Xbox` / `PS` button itself is not remappable; the system usually keeps it.

---

## When buttons do nothing

| Symptom | Likely cause |
|---|---|
| No HUD, nothing responds | the browser only reports a controller after a button press once the game is open; press any button |
| The character will not walk | the stick is pushed less than halfway, or you just pressed `X` and have not let the stick return to the centre |
| A skill does nothing on a moving monster | Quick-Cast is *Off* or *Release* and the cursor is no longer on it; use *Instant*, or aim with the right stick |
| Heal lands on the monster | a monster is selected and Instant Mode cast it there; `RS click` first |
| `Y` picks up the wrong item | nothing was selected, so it took the nearest; switch the D-pad to items with `LS click` |
| A button does something unexpected | it was remapped; check **Mapping**, or **Reset to defaults** |
| The cursor drifts on its own | raise **Axis Threshold** |
| `A` does nothing | **Disable Virtual Mouse** is on |
