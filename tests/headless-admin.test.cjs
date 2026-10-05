'use strict';
// Headless admin page (electron/headless/): Settings in a browser, for a host
// who is not at the machine. What has to hold: nothing answers without the
// printed token, a page on another site cannot call anything, the page gets
// the same handlers, and a handler's question reaches the browser and comes
// back as the answer.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const { RemoteDialogs } = require('../electron/headless/remote-dialogs');
const admin = require('../electron/headless/admin-server');

const SRC = path.join(__dirname, '..', 'src');

function request(port, { method = 'GET', path: p = '/', headers = {}, body } = {}) {
	return new Promise((resolve, reject) => {
		const req = http.request({ host: '127.0.0.1', port, method, path: p, headers: { Host: `127.0.0.1:${port}`, ...headers } }, res => {
			const chunks = [];
			res.on('data', c => chunks.push(c));
			res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks).toString('utf8') }));
		});
		req.on('error', reject);
		if (body !== undefined) req.write(body);
		req.end();
	});
}

async function withServer(invoke, fn) {
	const dialogs = new RemoteDialogs({ timeoutMs: 2000 });
	const uploadDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ro-admin-test-'));
	const server = await admin.start({ host: '127.0.0.1', port: 0, srcDir: SRC, invoke, dialogs, uploadDir, info: () => ({ gameUrl: 'http://127.0.0.1:3338/' }) });
	try {
		await fn(server, dialogs, uploadDir);
	} finally {
		await server.close();
		fs.rmSync(uploadDir, { recursive: true, force: true });
	}
}

async function signIn(server) {
	const r = await request(server.port, { path: `/settings?token=${server.token}` });
	assert.equal(r.status, 302);
	assert.equal(r.headers.location, '/settings', 'the token leaves the address bar');
	const cookie = r.headers['set-cookie'][0];
	assert.match(cookie, /HttpOnly/);
	assert.match(cookie, /SameSite=Strict/);
	return cookie.split(';')[0];
}

test('nothing answers without the token, and a wrong token is refused', async () => {
	await withServer(async () => 'x', async server => {
		assert.match(server.url, new RegExp(`^http://127\\.0\\.0\\.1:${server.port}/settings\\?token=`));
		assert.equal((await request(server.port, { path: '/settings' })).status, 401);
		assert.equal((await request(server.port, { path: '/settings?token=nope' })).status, 403);
		assert.equal((await request(server.port, { path: '/theme.css' })).status, 401);
		const call = await request(server.port, { method: 'POST', path: '/admin/api/invoke', headers: { 'X-RO-Admin': '1' }, body: '{"name":"get_settings"}' });
		assert.equal(call.status, 401);
	});
});

test('the token signs in, and the page is Settings with the bridge in front of its scripts', async () => {
	await withServer(async () => 'x', async server => {
		const cookie = await signIn(server);
		const page = await request(server.port, { path: '/settings', headers: { Cookie: cookie } });
		assert.equal(page.status, 200);
		const shim = page.body.indexOf('<script src="admin-shim.js">');
		assert.ok(shim > -1 && shim < page.body.indexOf('<script src="mods-state.js">'), 'the bridge loads before any page script');
		assert.equal((await request(server.port, { path: '/admin-shim.js', headers: { Cookie: cookie } })).status, 200);
		// Setup too, with the same bridge, for where the client's files are.
		const setup = await request(server.port, { path: '/setup', headers: { Cookie: cookie } });
		assert.equal(setup.status, 200);
		assert.ok(setup.body.indexOf('<script src="admin-shim.js">') > -1);
		// Only the pages' own files: nothing else under src/, nothing outside it.
		assert.equal((await request(server.port, { path: '/setup.html', headers: { Cookie: cookie } })).status, 404);
		assert.equal((await request(server.port, { path: '/index.html', headers: { Cookie: cookie } })).status, 404);
		assert.equal((await request(server.port, { path: '/../package.json', headers: { Cookie: cookie } })).status, 404);
	});
});

test('a call reaches the handlers, and a page on another site cannot make one', async () => {
	const calls = [];
	const invoke = async (name, args) => {
		calls.push([name, args]);
		if (name === 'boom') throw new Error('it broke');
		return { name };
	};
	await withServer(invoke, async server => {
		const cookie = await signIn(server);
		const ok = await request(server.port, { method: 'POST', path: '/admin/api/invoke', headers: { Cookie: cookie, 'X-RO-Admin': '1', 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'list_mods', args: { a: 1 } }) });
		assert.deepEqual(JSON.parse(ok.body), { ok: true, value: { name: 'list_mods' } });
		const failed = await request(server.port, { method: 'POST', path: '/admin/api/invoke', headers: { Cookie: cookie, 'X-RO-Admin': '1' }, body: JSON.stringify({ name: 'boom' }) });
		assert.deepEqual(JSON.parse(failed.body), { ok: false, error: 'it broke' });
		// A cross-site form sends the cookie but cannot add a header.
		const forged = await request(server.port, { method: 'POST', path: '/admin/api/invoke', headers: { Cookie: cookie }, body: JSON.stringify({ name: 'stack_down' }) });
		assert.equal(forged.status, 403);
		// A name of somebody else's pointed at this address (DNS rebinding).
		const rebound = await request(server.port, { path: '/settings', headers: { Cookie: cookie, Host: `evil.example:${server.port}` } });
		assert.equal(rebound.status, 421);
		assert.deepEqual(calls.map(c => c[0]), ['list_mods', 'boom']);
		// A script can use the token itself.
		const bearer = await request(server.port, { method: 'POST', path: '/admin/api/invoke', headers: { Authorization: `Bearer ${server.token}`, 'X-RO-Admin': '1' }, body: JSON.stringify({ name: 'stack_status' }) });
		assert.equal(JSON.parse(bearer.body).ok, true);
	});
});

test("a handler's question reaches the browser, and its answer comes back", async () => {
	const electronDialog = {};
	const dialogs = new RemoteDialogs({ timeoutMs: 2000 }).install(electronDialog);
	const asked = electronDialog.showMessageBox(null, { message: 'Install x?', buttons: ['Install', 'Cancel'], cancelId: 1 });
	const [q] = dialogs.pending();
	assert.equal(q.kind, 'message');
	assert.deepEqual(q.options.buttons, ['Install', 'Cancel']);
	assert.equal(dialogs.answer(q.id, 0), true);
	assert.deepEqual(await asked, { response: 0, checkboxChecked: false });
	assert.equal(dialogs.answer(q.id, 0), false, 'answered once');

	const open = electronDialog.showOpenDialog({ properties: ['openFile'] });
	dialogs.answer(dialogs.pending()[0].id, '/srv/mods/my-mod.zip');
	assert.deepEqual(await open, { canceled: false, filePaths: ['/srv/mods/my-mod.zip'] });

	const save = electronDialog.showSaveDialog({ defaultPath: 'backup.sql' });
	dialogs.answer(dialogs.pending()[0].id, null);
	assert.deepEqual(await save, { canceled: true, filePath: undefined });
});

test('a question nobody answers is cancelled, so a handler never hangs', async () => {
	const electronDialog = {};
	const dialogs = new RemoteDialogs({ timeoutMs: 50 }).install(electronDialog);
	const r = await electronDialog.showMessageBox({ message: 'Remove x?', buttons: ['Remove', 'Cancel'], cancelId: 1 });
	assert.equal(r.response, 1);
	assert.equal(dialogs.pending().length, 0);
});

test('an upload lands on the server under its own name, for a question to answer with', async () => {
	await withServer(async () => 'x', async (server, dialogs, uploadDir) => {
		const cookie = await signIn(server);
		const r = await request(server.port, { method: 'POST', path: `/admin/api/upload?name=${encodeURIComponent('../my mod.zip')}`, headers: { Cookie: cookie, 'X-RO-Admin': '1' }, body: 'PK\u0003\u0004zip' });
		const { path: saved } = JSON.parse(r.body);
		assert.equal(path.basename(saved), 'my mod.zip', 'a path in the name is dropped');
		assert.ok(saved.startsWith(uploadDir));
		assert.equal(fs.readFileSync(saved, 'utf8'), 'PK\u0003\u0004zip');
	});
});

test('main.js lets the admin page reach only what Settings calls', () => {
	const main = fs.readFileSync(path.join(__dirname, '..', 'electron', 'main.js'), 'utf8');
	const block = main.slice(main.indexOf('const HEADLESS_PAGE_HANDLERS'), main.indexOf(']);', main.indexOf('const HEADLESS_PAGE_HANDLERS')));
	const allowed = new Set([...block.matchAll(/'([a-z_0-9]+)'/g)].map(m => m[1]));
	// The game page's own calls and anything that opens a window stay out.
	for (const name of ['remember_login', 'mod_host_request', 'open_game', 'open_mod_settings', 'open_tool', 'open_setup', 'launch_game', 'copy_text']) {
		assert.ok(!allowed.has(name), `${name} must not be reachable from the admin page`);
	}
	// Everything the Settings page calls by a fixed name is either allowed or
	// done in the browser by the shim.
	const page = ['settings.html', 'accounts-settings.js', 'setup.html'].map(f => fs.readFileSync(path.join(SRC, f), 'utf8')).join('\n');
	const used = new Set([...page.matchAll(/invoke\(['"]([a-z_0-9]+)['"]/g)].map(m => m[1]));
	const inBrowser = new Set(['copy_text', 'open_game', 'open_setup', 'close_setup']);
	const headlessOnlyErrors = new Set(['open_mod_settings', 'open_tool', 'agent_open_guide']);
	for (const name of used) {
		if (inBrowser.has(name) || headlessOnlyErrors.has(name)) continue;
		assert.ok(allowed.has(name), `Settings calls ${name}, which the admin page cannot`);
	}
});
