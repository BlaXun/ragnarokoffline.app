'use strict';
// Settings -> Tools -> Map editor (#414): the app's half of it.
//
// The page is tools/map-editor/, served under ro-tool://map-editor/ like the
// other Tools. What it asks of its host -- the client's files, the mods, the
// server's tables, saving -- is answered by the same bridge the command line
// uses (tools/map-editor/server/bridge.js); this file adapts it to Electron's
// protocol handler and adds what only the app can do:
//
//   test          switch the mod on, restart the server, put a character on
//                 the map, reopen the game (Test in game)
//   characters    the player's characters, for Test in game
//   open-file     open a mod's dialogue file in the player's text editor
//
// It also runs the control server agents use: `ragnarok-map` and its MCP
// server read <state>/map-editor/connection.json (port and token, readable
// only by the user) and send commands to the open editor page. The first time
// the editor is opened in a session, that folder gets the launcher and the
// agent guide.

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { pathToFileURL } = require('node:url');

const ROOT = path.join(__dirname, '..', 'tools', 'map-editor');
const importEsm = rel => import(pathToFileURL(path.join(ROOT, rel)).href);

function shellQuote(s) { return `'${String(s).replace(/'/g, `'\\''`)}'`; }

/**
 * @param {object} deps
 *   stateDir(), runtimeDir(), assetPort(), net, shell, log(text),
 *   stackBin(), stackEnv(),
 *   test({ mod, map, x, y, char }) -> Promise<{ message }>  the app's Test in game
 *   openWindow(query, { show })   open (or focus) the editor window
 *   windowOpen() -> bool
 *   execPath                       the app binary, for the CLI launcher
 */
function createMapEditor(deps) {
	let bridge = null;
	let control = null;
	const dir = () => path.join(deps.stateDir(), 'map-editor');

	async function getBridge() {
		if (bridge) return bridge;
		const { createBridge, runStack } = await importEsm('server/bridge.js');
		const { env } = deps.stackEnv();
		bridge = createBridge({
			name: 'app',
			actions: ['test', 'characters', 'open-file'],
			stateDir: deps.stateDir,
			runtimeDir: deps.runtimeDir,
			repoDir: () => { const r = path.join(__dirname, '..'); return fs.existsSync(path.join(r, 'vendor')) ? r : null; },
			assetBase: () => `http://127.0.0.1:${deps.assetPort()}`,
			fetch: (url, init) => deps.net.fetch(url, { ...init, bypassCustomProtocolHandlers: true }),
			stack: (args, input) => runStack(deps.stackBin(), env, args, input),
			action,
			log: deps.log,
		});
		return bridge;
	}

	async function characters() {
		const { runCp } = require('./cp-bridge');
		const answer = await runCp(deps, { action: 'characters' }, 60000);
		const out = [];
		for (const a of answer.accounts || []) for (const c of a.characters || []) out.push({ char_id: c.char_id, name: c.name, base_level: c.base_level, last_map: c.last_map, account: a.username });
		return { characters: out };
	}

	async function action(name, body) {
		if (name === 'characters') return characters();
		if (name === 'test') {
			const { mod, map, x, y, char } = body || {};
			if (!/^[A-Za-z0-9_-]{1,64}$/.test(mod || '')) throw new Error('Save the map into a mod first.');
			if (!/^[a-z0-9_@-]{1,11}$/.test(map || '')) throw new Error('That is not a map name rAthena keeps.');
			return deps.test({ mod, map, x: Math.max(0, Math.round(Number(x) || 0)), y: Math.max(0, Math.round(Number(y) || 0)), char: char ? String(char) : null });
		}
		if (name === 'open-file') {
			const mod = String(body.mod || ''), rel = String(body.path || '');
			if (!/^[A-Za-z0-9_-]{1,64}$/.test(mod) || !/^npc\/[A-Za-z0-9_@.-]+\.txt$/.test(rel)) throw new Error('The map editor only opens a mod\'s npc/ scripts.');
			const file = path.join(deps.stateDir(), 'mods', mod, ...rel.split('/'));
			if (!fs.existsSync(file)) throw new Error(`${rel} is not there yet: save the map first.`);
			const err = await deps.shell.openPath(file);
			if (err) throw new Error(err);
			return { message: `Opened ${rel}. Save it, then Test in game to try the dialogue.`, file };
		}
		throw new Error(`no action ${name}`);
	}

	/** ro-tool://map-editor/<name>: the bridge's routes, or null for the page's own files. */
	async function route(name, url, request) {
		if (!name.startsWith('asset/') && !name.startsWith('api/')) return null;
		// Only the editor's own page, as the other Tools' bridges check.
		const origin = request.headers.get('origin');
		if (origin && origin !== 'ro-tool://map-editor') return new Response('not allowed', { status: 403 });
		if (name.startsWith('api/remote/') || name.startsWith('api/host/') || name === 'api/save' || name === 'api/prefabs') ensureControl().catch(e => deps.log(`map editor: control: ${e.message}`));
		const b = await getBridge();
		const body = request.method === 'POST' ? new Uint8Array(await request.arrayBuffer()) : null;
		const answer = await b.handle({ method: request.method, path: name, query: url.searchParams, body });
		if (!answer) return new Response('not found', { status: 404 });
		return new Response(answer.body, { status: answer.status, headers: { 'content-type': answer.type, 'cache-control': answer.cache || 'no-store' } });
	}

	/** The launcher a terminal or an MCP client runs: the app's own binary, as Node, on a copy of the CLI. */
	function writeLauncher() {
		const cliDir = path.join(dir(), 'cli');
		// The editor's folder, copied out of the app (asar) so plain Node can read it.
		fs.rmSync(cliDir, { recursive: true, force: true });
		fs.cpSync(ROOT, cliDir, { recursive: true });
		const cli = path.join(cliDir, 'cli.js');
		const bin = deps.execPath;
		if (process.platform === 'win32') {
			const file = path.join(dir(), 'ragnarok-map.cmd');
			fs.writeFileSync(file, `@echo off\r\nset "ELECTRON_RUN_AS_NODE=1"\r\nset "RAGNAROKMAC_STATE=${deps.stateDir()}"\r\n"${bin}" "${cli}" %*\r\n`);
			return file;
		}
		const file = path.join(dir(), 'ragnarok-map');
		fs.writeFileSync(file, `#!/bin/sh\n# Ragnarok Offline's map editor from the command line. See AGENTS.md beside this file.\nELECTRON_RUN_AS_NODE=1 RAGNAROKMAC_STATE=${shellQuote(deps.stateDir())} exec ${shellQuote(bin)} ${shellQuote(cli)} "$@"\n`, { mode: 0o755 });
		try { fs.chmodSync(file, 0o755); } catch { /* ignore */ }
		return file;
	}

	/** The control server agents talk to, started once per session. */
	async function ensureControl() {
		if (control) return control;
		control = (async () => {
			const b = await getBridge();
			const { startServer, writePrivate } = await importEsm('server/http.js');
			fs.mkdirSync(dir(), { recursive: true });
			const file = path.join(dir(), 'connection.json');
			let previous = null;
			try { previous = JSON.parse(fs.readFileSync(file, 'utf8')); } catch { /* first time */ }
			const token = previous && previous.app && /^[0-9a-f]{64}$/.test(previous.token || '') ? previous.token : crypto.randomBytes(32).toString('hex');
			const commands = {
				// Open the editor window for an agent, shown or not.
				'editor.open': async ({ mod, map, show } = {}) => {
					const query = new URLSearchParams();
					if (mod) query.set('mod', String(mod));
					if (map) query.set('map', String(map));
					await deps.openWindow(query.toString(), { show: show !== false });
					return { opened: true };
				},
			};
			let server;
			for (const port of [previous && previous.app ? previous.port : null, 7491, 0].filter(p => p !== null && p !== undefined)) {
				try { server = await startServer({ bridge: null, remote: b.remote, root: ROOT, token, port, log: deps.log, commands }); break; } catch { /* taken */ }
			}
			if (!server) throw new Error('could not open a local port for the map editor');
			let command = null;
			try { command = writeLauncher(); } catch (e) { deps.log(`map editor: could not write the launcher: ${e.message}`); }
			try { fs.copyFileSync(path.join(ROOT, 'AGENTS.md'), path.join(dir(), 'AGENTS.md')); } catch (e) { deps.log(`map editor: could not write AGENTS.md: ${e.message}`); }
			writePrivate(file, JSON.stringify({ app: true, port: server.port, token, command, guide: path.join(dir(), 'AGENTS.md'), mcp: command ? { command, args: ['mcp'] } : null }, null, 2) + '\n');
			deps.log(`map editor: agents can connect on 127.0.0.1:${server.port} (${file})`);
			return server;
		})();
		try { return await control; } catch (e) { control = null; throw e; }
	}

	async function shutdown() {
		if (!control) return;
		try { const s = await control; await s.close(); } catch { /* never started */ }
		control = null;
	}

	return { route, ensureControl, shutdown, getBridge };
}

module.exports = { createMapEditor, MAP_EDITOR_ROOT: ROOT };
