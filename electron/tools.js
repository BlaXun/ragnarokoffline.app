'use strict';
// Settings -> Tools (#195): small pages that help while making mods, opened
// in their own windows and fed from the running server.
//
// The pages are self-contained HTML (tools/<id>/), written to work from a
// folder with files dropped on them. Here they are served from the app under
// ro-tool://<id>/, and the files they would look for next to themselves are
// answered from the server instead, so nothing needs extracting by hand and
// nothing needs Python:
//
//   ro-tool://mob-browser/mob_db.yml        ragnarok-stack export-table mob_db
//   ro-tool://mob-browser/item_db_*.yml     ... item_db_equip / _etc / _usable
//   ro-tool://item-browser/itemInfo.lua     the client's item table, as served
//   http://127.0.0.1:3338/item-icons.js     AegisName -> icon, built here
//
// The tables come with the mods' db/import laid over them, so a mod's
// monsters and items show up too. Each window has its own session and no
// preload: a tool page cannot reach the app.

const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');

const SCHEME = 'ro-tool';
const PARTITION = 'persist:ro-tools';
const ROOT = path.join(__dirname, '..', 'tools');

const TOOLS = [
	{
		id: 'item-browser',
		name: 'Item browser',
		description: 'Every item the game client knows: names, descriptions, icons and slots, grouped by type.',
		page: 'item-browser.html',
		author: 'BlaXun',
		// The page loads a dropped itemInfo.lua; hand it the one the client uses.
		feed: 'itemInfo.lua',
	},
	{
		id: 'mob-browser',
		name: 'Monster browser',
		description: 'Every monster on your server, mods included: stats, skills, drops with their icons, MVPs.',
		page: 'mob-browser.html',
		author: 'BlaXun',
		needsServer: true,
	},
];

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.yml': 'text/yaml; charset=utf-8', '.lua': 'application/octet-stream', '.png': 'image/png', '.json': 'application/json' };

// Registered before the app is ready: a standard, secure scheme, so relative
// URLs and fetch() work in the pages the way they would over HTTP.
const schemePrivileges = { scheme: SCHEME, privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true } };

/**
 * @param {object} deps
 *   BrowserWindow, session, net, shell, stackBin(), stackEnv(), stateDir(), log(text), icon
 */
function createTools(deps) {
	const windows = new Map();
	let handlersReady = false;

	function exportTable(name) {
		const { cwd, env } = deps.stackEnv();
		return new Promise((resolve, reject) => {
			execFile(deps.stackBin(), ['export-table', name], { cwd, env, timeout: 60000, maxBuffer: 64 * 1024 * 1024 }, (error, stdout, stderr) => {
				if (error) reject(new Error((stderr || '').trim() || error.message));
				else resolve(stdout);
			});
		});
	}

	// The client's item table, the one the game itself reads.
	function itemInfo() {
		const dir = path.join(deps.stateDir(), 'assets', 'System');
		for (const name of ['itemInfo.lua', 'itemInfo.lub', 'itemInfo_true.lua', 'itemInfo_true.lub']) {
			const file = path.join(dir, name);
			if (fs.existsSync(file)) return fs.readFileSync(file);
		}
		throw new Error('The client\'s item table is not there yet. Start the game once, then try again.');
	}

	// AegisName -> icon name, for the monster browser's drops: the server's
	// item tables give AegisName -> id, the client's gives id -> icon.
	async function itemIcons() {
		const ids = new Map();
		for (const table of ['item_db_equip', 'item_db_etc', 'item_db_usable']) {
			const text = await exportTable(table);
			for (const m of text.matchAll(/(?:^|\n) {2}- Id:\s*(\d+)([\s\S]*?)(?=\n {2}- Id:|\n\S|$)/g)) {
				const aegis = /\bAegisName:\s*(\S+)/.exec(m[2]);
				if (aegis) ids.set(aegis[1], Number(m[1]));
			}
		}
		const raw = itemInfo();
		let text;
		try { text = new TextDecoder('utf-8', { fatal: true }).decode(raw); } catch { text = new TextDecoder('euc-kr').decode(raw); }
		const icons = new Map();
		for (const m of text.matchAll(/\[\s*(\d+)\s*\]\s*=\s*\{/g)) {
			const chunk = text.slice(m.index, m.index + 4000);
			const res = /\bidentifiedResourceName\s*=\s*"([^"]*)"/.exec(chunk);
			if (res && res[1]) icons.set(Number(m[1]), res[1]);
		}
		const out = {};
		for (const [aegis, id] of ids) if (icons.has(id)) out[aegis] = icons.get(id);
		return 'window.__mobItemIcons=' + JSON.stringify(out) + ';if(window.__mobItemIconsReady)window.__mobItemIconsReady();\n';
	}

	function respond(body, type, status = 200) {
		return new Response(body, { status, headers: { 'content-type': type, 'cache-control': 'no-store' } });
	}

	function setupSession() {
		if (handlersReady) return;
		const ses = deps.session.fromPartition(PARTITION);
		ses.protocol.handle(SCHEME, async request => {
			const url = new URL(request.url);
			const tool = TOOLS.find(t => t.id === url.hostname);
			if (!tool) return respond('no such tool', 'text/plain', 404);
			const name = decodeURIComponent(url.pathname.replace(/^\/+/, ''));
			try {
				if (name === 'mob_db.yml' || /^item_db_(equip|etc|usable)\.yml$/.test(name)) {
					return respond(await exportTable(name.replace(/\.yml$/, '')), TYPES['.yml']);
				}
				if (name === 'itemInfo.lua') return respond(itemInfo(), TYPES['.lua']);
				// The tool's own files, and nothing outside its folder.
				const dir = path.join(ROOT, tool.id);
				const file = path.resolve(dir, name || tool.page);
				if (!file.startsWith(dir + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) return respond('not found', 'text/plain', 404);
				return respond(fs.readFileSync(file), TYPES[path.extname(file)] || 'application/octet-stream');
			} catch (e) {
				deps.log(`tools: ${tool.id} ${name}: ${e.message}`);
				return respond(e.message, 'text/plain', 503);
			}
		});
		// The monster browser loads its icon map from the asset server, where
		// the old extraction script used to leave it. Answer that one URL here
		// and let everything else through.
		ses.protocol.handle('http', async request => {
			const url = new URL(request.url);
			if (url.host === '127.0.0.1:3338' && url.pathname === '/item-icons.js') {
				try { return respond(await itemIcons(), TYPES['.js']); } catch (e) {
					deps.log(`tools: item icons: ${e.message}`);
					return respond('/* ' + e.message.replace(/\*\//g, '') + ' */', TYPES['.js'], 503);
				}
			}
			return deps.net.fetch(request, { bypassCustomProtocolHandlers: true });
		});
		handlersReady = true;
	}

	async function open(id) {
		const tool = TOOLS.find(t => t.id === id);
		if (!tool) throw new Error(`No tool called ${id}`);
		const existing = windows.get(id);
		if (existing && !existing.isDestroyed()) { existing.focus(); return; }
		setupSession();
		const ses = deps.session.fromPartition(PARTITION);
		// The pages cache what they parsed and restore it before looking for
		// anything newer. Start them clean, so a mod added since shows up.
		await ses.clearStorageData({ storages: ['indexdb'] }).catch(() => {});
		const win = new deps.BrowserWindow({
			width: 1280, height: 860,
			title: `${tool.name} — Ragnarok Offline`,
			icon: deps.icon,
			webPreferences: { partition: PARTITION, contextIsolation: true, nodeIntegration: false, sandbox: true },
		});
		windows.set(id, win);
		win.on('closed', () => windows.delete(id));
		win.on('page-title-updated', e => e.preventDefault());
		win.webContents.setWindowOpenHandler(({ url }) => {
			// Links out (rAthena docs, GitHub) open in the browser, not here.
			if (/^https?:\/\//.test(url)) deps.shell.openExternal(url);
			return { action: 'deny' };
		});
		win.webContents.on('will-navigate', event => {
			if (!event.url.startsWith(`${SCHEME}://${id}/`)) event.preventDefault();
		});
		await win.loadURL(`${SCHEME}://${id}/${tool.page}`);
		if (tool.feed) {
			// The page's own loader, with the file it would have been handed.
			const result = await win.webContents.executeJavaScript(`(async () => {
				if (typeof loadFile !== 'function') return 'this page has no loader';
				const res = await fetch('./${tool.feed}', { cache: 'no-store' });
				if (!res.ok) return await res.text();
				await loadFile(new File([await res.blob()], '${tool.feed}'));
				return 'ok';
			})()`).catch(e => e.message);
			if (result !== 'ok') deps.log(`tools: ${id}: ${result}`);
		}
	}

	return {
		list: () => TOOLS.map(({ id, name, description, author, needsServer }) => ({ id, name, description, author, needsServer: !!needsServer })),
		open,
	};
}

module.exports = { createTools, schemePrivileges, SCHEME, TOOLS };
