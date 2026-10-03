// Guards for Assumptio on party members (#290).
//
// HP_ASSUMPTIO is a single-target Support skill (TargetType: Support, Hit: Single), but every
// curated row for it was `Target: self`, so a High Priest companion only ever cast it on itself.
// The ally row has to come first: the rotation walks rows in order, and the self row's
// `not_self_status` gate is satisfied as soon as the companion lacks the buff.
//
// An ally row is seeded only when the companion has learned the skill (pc_checkskill in the
// attack rotation), unlike a self row, which casts from the YAML level alone. A non-transcendent
// Arch Bishop (4057) inherits Priest, not High_Priest, so it never learns Assumptio; an ally row
// there would never load, and it is left with its self row.
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');

const ROOT = path.join(__dirname, '..');
const YAML = path.join(ROOT, 'third-party', 'population-engine', 'files', 'db', 'population_skill_db.yml');
const yaml = fs.readFileSync(YAML, 'utf8').replace(/\r\n/g, '\n');

function block(jobId) {
	const m = new RegExp(`\\n  - JobId: ${jobId}\\n    Skills:\\n`).exec(yaml);
	assert.ok(m, `job ${jobId} must have a curated block`);
	const start = m.index + m[0].length;
	const next = yaml.indexOf('\n  - JobId: ', start);
	return yaml.slice(start, next < 0 ? yaml.length : next);
}

const ALLY = /\{ SkillId: HP_ASSUMPTIO,\s+Level: 5,\s+Rate: 10000, Target: ally, Condition: not_ally_status, CondValue: SC_ASSUMPTIO \}/;
const SELF = /\{ SkillId: HP_ASSUMPTIO,\s+Level: 5,\s+Rate: 10000, Target: self, Condition: not_self_status, CondValue: SC_ASSUMPTIO \}/;

test('High Priest and transcendent Arch Bishop cast Assumptio on party members before themselves', () => {
	for (const jobId of [4009, 4063]) {
		const body = block(jobId);
		const ally = ALLY.exec(body);
		const self = SELF.exec(body);
		assert.ok(ally, `job ${jobId} must carry an ally Assumptio row`);
		assert.ok(self, `job ${jobId} keeps its self Assumptio row`);
		assert.ok(ally.index < self.index, `job ${jobId}: the ally row must come before the self row`);
	}
});

test('a non-transcendent Arch Bishop gets no ally Assumptio row it could never learn', () => {
	assert.ok(!ALLY.test(block(4057)));
});
