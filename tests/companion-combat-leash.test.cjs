// Guards against companions pacing between a monster and their owner (#290 testing).
//
// Combat takes monsters up to 12 cells from the owner, but the follow walked a companion back as
// soon as it was 5 cells away. It set off for a monster 8 cells out, turned back at the fifth
// cell, took the monster again, and paced back and forth until the owner came closer. While it
// fights a monster inside the combat radius, the follow now lets it go as far as the fight takes
// it; once the monster is left behind, the leash is 4 cells again.
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');

const engine = fs.readFileSync(path.join(__dirname, '..', 'third-party', 'population-engine', 'files', 'src',
	'map', 'population_engine.cpp'), 'utf8').replace(/\r\n/g, '\n');

function fn(name) {
	const start = engine.indexOf(name);
	assert.ok(start >= 0, `${name} must exist`);
	return engine.slice(start, engine.indexOf('\n}\n', start));
}

test('combat and follow share one radius', () => {
	assert.match(engine, /static constexpr int kCompanionCombatRadius = 12;/);
	const combat = fn('static uint32 pop_companion_combat_target(');
	assert.match(combat, /owner_distance > kCompanionCombatRadius/);
});

test('the follow leash widens while the companion fights inside the radius', () => {
	const follow = fn('static bool pop_companion_follow_owner(');
	assert.match(follow, /int leash = 4;/);
	assert.match(follow, /check_distance_bl\(owner, target, kCompanionCombatRadius\)\)\s*leash = kCompanionCombatRadius \+ 2;/);
	assert.match(follow, /return sd->m == owner->m && check_distance_bl\(sd, owner, leash\);/, 'the throttled path too');
	assert.match(follow, /if \(owner_distance > leash\) \{/);
	assert.ok(!/owner_distance > 4\b/.test(follow), 'no fixed 4-cell leash left');
});
