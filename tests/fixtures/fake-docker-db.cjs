#!/usr/bin/env node
'use strict';
// A stand-in for docker-slim with just enough of a `ragnarok-db` container
// behind it for `ragnarok-stack db` (tests/db-browser-transport.test.cjs).
//
// The database is rAthena's `char` table (tests/fixtures/rathena-char-table.sql)
// with the rows in $FAKE_DB, answering the statements stack/src/database.rs
// builds. Two ways in, as on the real thing:
//
//   exec -i ragnarok-db mariadb ...          the answer on exec's stdout, put
//                                            through docker-slim's demux as it
//                                            is at the pinned commit: framed by
//                                            the daemon, read back 8 KiB at a
//                                            time, a frame that straddles two
//                                            reads dropped
//   exec -i ragnarok-db sh -c '... > /backups/x 2> /backups/y'
//                                            the answer in a file under
//                                            $FAKE_STATE/backups, which is
//                                            where /backups is mounted
const fs = require('node:fs');
const path = require('node:path');

const args = process.argv.slice(2);
const state = process.env.FAKE_STATE;
const dbFile = process.env.FAKE_DB;
const backups = path.join(state, 'backups');
// The container's own /tmp, where backups are dumped before `docker cp` brings them out.
const containerTmp = path.join(state, 'container-tmp');
fs.mkdirSync(containerTmp, { recursive: true });
const inContainer = file => (file.startsWith('/tmp/') ? path.join(containerTmp, path.basename(file)) : path.join(backups, path.basename(file)));
const hex = s => Buffer.from(s, 'utf8').toString('hex').toUpperCase();
const unhex = h => Buffer.from(h, 'hex').toString('utf8');

function columns() {
	const sql = fs.readFileSync(path.join(__dirname, 'rathena-char-table.sql'), 'utf8');
	return sql.split('\n').filter(l => l.startsWith('  `')).map(line => {
		const [, name, rest] = line.match(/^ {2}`([^`]+)` (.*)$/);
		const lower = rest.toLowerCase();
		const typeWord = lower.split(/\s+/)[0];
		const def = rest.match(/default '([^']*)'/i);
		return {
			name,
			type: lower.includes(' unsigned') ? `${typeWord} unsigned` : typeWord,
			dataType: typeWord.split('(')[0],
			nullable: !lower.includes('not null'),
			default: def ? `'${def[1]}'` : (lower.includes('default null') ? 'NULL' : null),
			extra: lower.includes('auto_increment') ? 'auto_increment' : '',
		};
	});
}

function cell(v) { return v === null ? 'NULL' : hex(v); }

function answer(sql) {
	const db = JSON.parse(fs.readFileSync(dbFile, 'utf8'));
	const cols = columns();
	const out = [];
	for (const line of sql.split('\n')) {
		let m;
		if (/information_schema\.TABLES/.test(line)) {
			for (const [name, rows] of [['char', db.rows.length], ['inventory', 0], ['login', 2]]) out.push(`t\t${hex(name)}\t${rows}\t${hex('MyISAM')}`);
		} else if (/information_schema\.STATISTICS/.test(line) && /SELECT 'k', HEX\(TABLE_NAME\)/.test(line)) {
			out.push(`k\t${hex('char')}\t${hex('char_id')}`, `k\t${hex('inventory')}\t${hex('id')}`, `k\t${hex('login')}\t${hex('account_id')}`);
		} else if ((m = line.match(/information_schema\.COLUMNS .*TABLE_NAME = X'([0-9A-F]*)'/))) {
			if (unhex(m[1]) === 'char') {
				for (const c of cols) out.push(['c', hex(c.name), hex(c.type), hex(c.dataType), c.nullable ? 'YES' : 'NO', c.default === null ? 'NULL' : hex(c.default), hex(c.extra)].join('\t'));
			}
		} else if ((m = line.match(/information_schema\.STATISTICS .*TABLE_NAME = X'([0-9A-F]*)'/))) {
			if (unhex(m[1]) === 'char') out.push(`k\t${hex('char_id')}`);
		} else if (/^SELECT 'c', COUNT\(\*\) FROM `char`;$/.test(line)) {
			out.push(`c\t${db.rows.length}`);
		} else if ((m = line.match(/^SELECT 'r', .* FROM `char` ORDER BY `char_id` LIMIT (\d+) OFFSET (\d+);$/))) {
			const rows = [...db.rows].sort((a, b) => Number(a[0]) - Number(b[0])).slice(Number(m[2]), Number(m[2]) + Number(m[1]));
			for (const r of rows) out.push(['r', ...r.map(cell)].join('\t'));
		} else if ((m = line.match(/^SELECT (\d+), x\.\* FROM \(SELECT 1 FROM `char` WHERE `char_id` = (\d+) LIMIT 2\) AS x;$/))) {
			if (db.rows.some(r => r[0] === m[2])) out.push(`${m[1]}\t1`);
		} else if ((m = line.match(/^DELETE FROM `char` WHERE `char_id` = (\d+) LIMIT 1;$/))) {
			db.rows = db.rows.filter(r => r[0] !== m[1]);
			fs.writeFileSync(dbFile, JSON.stringify(db));
		} else if ((m = line.match(/^SELECT '([a-z-]+)';$/))) {
			out.push(m[1]);
		}
	}
	return out.length ? out.join('\n') + '\n' : '';
}

// slimd frames each read of the process's stdout; slim-client reads its
// socket 8 KiB at a time and demultiplexes every read on its own
// (slim-client/src/http.rs demux_stdcopy).
function throughSlimExec(text) {
	const bytes = Buffer.from(text, 'utf8');
	const frames = [];
	for (let i = 0; i < bytes.length; i += 4096) {
		const payload = bytes.subarray(i, i + 4096);
		const head = Buffer.alloc(8);
		head[0] = 1;
		head.writeUInt32BE(payload.length, 4);
		frames.push(head, payload);
	}
	const wire = Buffer.concat(frames);
	const out = [];
	for (let r = 0; r < wire.length; r += 8192) {
		const read = wire.subarray(r, r + 8192);
		let i = 0;
		while (i + 8 <= read.length) {
			const stream = read[i];
			const len = read.readUInt32BE(i + 4);
			i += 8;
			if (i + len > read.length) break;
			if (stream !== 2) out.push(read.subarray(i, i + len));
			i += len;
		}
	}
	return Buffer.concat(out);
}

const stdin = () => { try { return fs.readFileSync(0, 'utf8'); } catch { return ''; } };
const [verb] = args;

if (verb === 'capabilities') { process.stdout.write('exec-stdin-eof-v1\n'); process.exit(0); }
if (verb === 'inspect') {
	const name = args[args.length - 1];
	if (name !== 'ragnarok-db') { process.stderr.write(`No such container: ${name}\n`); process.exit(1); }
	if (args.includes('-f')) { process.stdout.write('running\n'); process.exit(0); }
	process.stdout.write(JSON.stringify([{ State: { Status: 'running', StartedAt: '2026-10-01T00:00:00.000000000Z' },
		Mounts: [{ Destination: '/var/lib/mysql', Type: 'volume', Name: 'ragnarokmac-db' }] }]));
	process.exit(0);
}
if (verb === 'exec') {
	const rest = args.slice(1).filter(a => a !== '-i');
	const [container, program, ...more] = rest;
	if (container !== 'ragnarok-db') process.exit(1);
	if (program === 'mariadb') { process.stdout.write(throughSlimExec(answer(stdin()))); process.exit(0); }
	if (program === 'rm') {
		for (const f of more.filter(a => a.startsWith('/backups/') || a.startsWith('/tmp/'))) fs.rmSync(inContainer(f), { force: true });
		process.exit(0);
	}
	if (program === 'sh' && more[0] === '-c') {
		const command = more[1];
		const target = command.match(/> (\/(?:backups|tmp)\/[A-Za-z0-9._-]+)/);
		if (!target) process.exit(2);
		if (/mariadb-dump /.test(command)) {
			fs.writeFileSync(inContainer(target[1]), '-- fake dump of `char`\n' + fs.readFileSync(dbFile, 'utf8'));
			process.exit(0);
		}
		const errors = command.match(/2> \/backups\/([A-Za-z0-9._-]+)/);
		fs.writeFileSync(inContainer(target[1]), answer(stdin()));
		if (errors) fs.writeFileSync(path.join(backups, errors[1]), '');
		process.exit(0);
	}
	process.exit(1);
}
// docker cp ragnarok-db:/tmp/<dump> <name>, run from the destination folder.
if (verb === 'cp' && args[1] && args[1].startsWith('ragnarok-db:')) {
	const from = inContainer(args[1].slice('ragnarok-db:'.length));
	if (!fs.existsSync(from)) process.exit(1);
	fs.copyFileSync(from, path.resolve(process.cwd(), args[2]));
	process.exit(0);
}
// ps, stop, start, logs: nothing is running but the database.
process.exit(0);
