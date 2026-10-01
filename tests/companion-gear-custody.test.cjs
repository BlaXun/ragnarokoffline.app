// Items a player hands a companion are still the player's. These guards pin the custody rules:
// an item that leaves a companion lands in the owner's bag or at the owner's feet, never nowhere.
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');

const ROOT = path.join(__dirname, '..');
const ENGINE = path.join(ROOT, 'third-party', 'population-engine', 'files', 'src', 'map', 'population_engine.cpp');
const engine = fs.readFileSync(ENGINE, 'utf8').replace(/\r\n/g, '\n');

function functionBody(signature) {
	const i = engine.indexOf(signature);
	assert.ok(i >= 0, `expected to find ${signature}`);
	const rest = engine.slice(i);
	const end = rest.indexOf('\n}\n');
	return end > 0 ? rest.slice(0, end + 3) : rest;
}

const HAND_BACK = 'static bool pop_companion_hand_back(';

test('the one hand-back path deletes from the companion only after the item has landed', () => {
	const body = functionBody(HAND_BACK);
	const del = body.indexOf('pc_delitem(');
	assert.ok(del > 0, 'hand-back must remove the item from the companion');
	const add = body.indexOf('pc_additem(owner');
	const floor = body.indexOf('map_addflooritem(');
	assert.ok(add > 0 && floor > 0 && add < del && floor < del,
		'the owner\'s bag, then the owner\'s feet, must both be tried before the companion lets go');
	assert.match(body.slice(floor, del), /return false;/,
		'when neither works the item must stay on the companion, not be deleted');
});

test('the trade and gear-return paths go through hand-back instead of deleting themselves', () => {
	for (const sig of ['void population_engine_companion_equip_traded(', 'int population_engine_companion_return_gear(']) {
		const body = functionBody(sig);
		assert.ok(!/pc_delitem\(/.test(body), `${sig} must not delete items itself`);
		assert.ok(body.includes('pop_companion_hand_back('), `${sig} must return items through hand-back`);
	}
});
