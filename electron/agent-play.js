'use strict';
// "Let an AI agent play with me" (#187): everything the setting turns on.
//
//   - the local API (agent-api.js), on while the setting is;
//   - <state>/agent/: connection.json (port + token, readable only by the
//     user), a `ragnarok-agent` launcher for the CLI, and AGENT.md, the guide
//     an agent is pointed at;
//   - the agent's own game window, made the first time a command needs it,
//     logged in as the app's `aiagent` account on the player's own server.
//
// The window has no preload and its own session, so the page in it cannot
// reach the app, and its client cache and settings are its own.

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { AgentDriver } = require('./agent-driver');
const { createAgentApi } = require('./agent-api');

const PARTITION = 'persist:ai-agent';
const DEFAULT_PORT = 7490;

function shellQuote(s) { return `'${String(s).replace(/'/g, `'\\''`)}'`; }

// A file only the user can read. POSIX mode bits; on Windows the state folder
// is under the user's own profile, whose ACL already says the same.
function writePrivate(file, text) {
	const tmp = `${file}.${crypto.randomBytes(6).toString('hex')}.tmp`;
	fs.writeFileSync(tmp, text, { mode: 0o600 });
	fs.renameSync(tmp, file);
	try { fs.chmodSync(file, 0o600); } catch { /* Windows */ }
}

/**
 * @param {object} deps
 *   BrowserWindow, stateDir(), stackBin(), gameBase() -> 'http://127.0.0.1:3338',
 *   gamePath, runAccount(request) -> Promise, era() -> 'renewal'|'prerenewal',
 *   hosting() -> bool (false when this app joins someone else's server),
 *   icon, log(text)
 */
function createAgentPlay(deps) {
	const dir = () => path.join(deps.stateDir(), 'agent');
	const connectionFile = () => path.join(dir(), 'connection.json');
	let api = null, port = null, token = null;
	let win = null, driver = null, credentials = null, opening = null;
	let visible = true;

	function readConnection() {
		try { return JSON.parse(fs.readFileSync(connectionFile(), 'utf8')); } catch { return null; }
	}

	function launcher() {
		const bin = deps.stackBin();
		if (process.platform === 'win32') {
			const file = path.join(dir(), 'ragnarok-agent.cmd');
			fs.writeFileSync(file, `@echo off\r\nset "RAGNAROKMAC_STATE=${deps.stateDir()}"\r\n"${bin}" agent %*\r\n`);
			return file;
		}
		const file = path.join(dir(), 'ragnarok-agent');
		fs.writeFileSync(file, `#!/bin/sh\n# Ragnarok Offline's AI agent command line. See AGENT.md beside this file.\nRAGNAROKMAC_STATE=${shellQuote(deps.stateDir())} exec ${shellQuote(bin)} agent "$@"\n`, { mode: 0o755 });
		try { fs.chmodSync(file, 0o755); } catch { /* ignore */ }
		return file;
	}

	async function start({ show = true } = {}) {
		visible = show;
		if (win && !win.isDestroyed()) { if (visible) win.show(); else win.hide(); }
		if (api) return info();
		fs.mkdirSync(dir(), { recursive: true });
		const previous = readConnection();
		// The same token and port as last time, so an agent set up once keeps
		// working across restarts; replaceToken() is how to revoke it.
		token = previous?.token && /^[0-9a-f]{64}$/.test(previous.token) ? previous.token : crypto.randomBytes(32).toString('hex');
		api = createAgentApi({ run, token, log: deps.log });
		for (const candidate of [previous?.port, DEFAULT_PORT, 0].filter(p => p !== undefined && p !== null)) {
			try { port = await api.listen(candidate); break; } catch { api.server.close(); api = createAgentApi({ run, token, log: deps.log }); }
		}
		if (!port) { api = null; throw new Error('Could not open a local port for the agent.'); }
		const command = launcher();
		writePrivate(connectionFile(), JSON.stringify({
			port, token,
			mcp: `http://127.0.0.1:${port}/mcp`,
			command,
			guide: path.join(dir(), 'AGENT.md'),
		}, null, 2) + '\n');
		try { fs.copyFileSync(path.join(__dirname, 'AGENT.md'), path.join(dir(), 'AGENT.md')); } catch (e) { deps.log(`agent: could not write AGENT.md: ${e.message}`); }
		deps.log(`agent play on: listening on 127.0.0.1:${port}`);
		return info();
	}

	async function stop({ disableAccount = true } = {}) {
		if (win && !win.isDestroyed()) win.destroy();
		win = null; driver = null; credentials = null;
		if (api) { await api.close().catch(() => {}); api = null; }
		// The file is how the CLI knows the agent is on; the token stays valid
		// only while it is there.
		fs.rmSync(connectionFile(), { force: true });
		if (disableAccount && deps.hosting()) {
			await deps.runAccount({ action: 'agent-disable', era: deps.era() }).catch(e => deps.log(`agent: could not disable the account: ${e.message}`));
		}
		deps.log('agent play off');
	}

	async function replaceToken() {
		const show = visible;
		await stop({ disableAccount: false });
		fs.mkdirSync(dir(), { recursive: true });
		writePrivate(connectionFile(), JSON.stringify({ port }, null, 2));
		return start({ show });
	}

	function info() {
		const c = readConnection() || {};
		return {
			on: Boolean(api),
			port: c.port, mcp: c.mcp, command: c.command, guide: c.guide, folder: dir(), connection: connectionFile(),
			token: c.token,
			windowOpen: Boolean(win && !win.isDestroyed()),
			claudeCommand: c.mcp ? `claude mcp add --transport http ragnarok-offline ${c.mcp} --header "Authorization: Bearer ${c.token}"` : null,
		};
	}

	// The agent's window, made on first use. Its account is (re)keyed each
	// time with a fresh password that is never written down.
	async function ensureWindow() {
		if (win && !win.isDestroyed() && driver) return driver;
		if (opening) return opening;
		opening = (async () => {
			if (!deps.hosting()) throw new Error('The player is joining someone else\'s server; the AI agent can only play on the player\'s own server.');
			const base = deps.gameBase();
			const up = await fetch(base, { signal: AbortSignal.timeout(3000) }).then(r => r.ok, () => false);
			if (!up) throw new Error('The game server is not running. Ask the player to press Play in Ragnarok Offline, then try again.');
			const password = crypto.randomBytes(12).toString('hex');
			await deps.runAccount({ action: 'agent', era: deps.era(), password });
			credentials = { user: 'aiagent', pass: password };

			win = new deps.BrowserWindow({
				width: 1280, height: 800, useContentSize: true,
				show: visible,
				title: 'AI agent — Ragnarok Offline',
				icon: deps.icon,
				webPreferences: {
					partition: PARTITION,
					contextIsolation: true,
					nodeIntegration: false,
					sandbox: true,
					// The agent plays whether or not its window is in front, or
					// shown at all.
					backgroundThrottling: false,
				},
			});
			// Muted: the player hears their own game, not a second copy of
			// its music and sounds from a window they may not even see.
			win.webContents.setAudioMuted(true);
			win.on('page-title-updated', e => e.preventDefault());
			win.webContents.on('will-prevent-unload', e => e.preventDefault());
			win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
			const allowed = new URL(base).origin;
			const guard = event => {
				try { if (new URL(event.url).origin !== allowed) event.preventDefault(); } catch { event.preventDefault(); }
			};
			win.webContents.on('will-navigate', guard);
			win.webContents.on('will-redirect', guard);
			win.on('closed', () => { win = null; driver = null; });
			driver = new AgentDriver(win.webContents, { shotsDir: path.join(dir(), 'screenshots'), credentials: async () => credentials });

			await win.loadURL(base + deps.gamePath);
			// The client's agent hook (window.roAgent) installs only when the
			// page opted in before it booted. This session is the agent's
			// own, so set the switch once and boot again; it persists.
			const hooked = await win.webContents.executeJavaScript(`localStorage.getItem('roAgent') === '1'`).catch(() => false);
			if (!hooked) {
				await win.webContents.executeJavaScript(`localStorage.setItem('roAgent', '1')`);
				await win.loadURL(base + deps.gamePath);
			}
			deps.log('agent: game window open');
			return driver;
		})();
		try { return await opening; } catch (e) {
			if (win && !win.isDestroyed()) win.destroy();
			win = null; driver = null;
			throw e;
		} finally { opening = null; }
	}

	async function run(cmd, args) {
		if (cmd === 'status' && !(win && !win.isDestroyed())) return { ok: true, window: false, next: 'login opens the agent\'s game window' };
		const d = await ensureWindow();
		return d.commands()[cmd](args);
	}

	function setVisible(show) {
		visible = show;
		if (win && !win.isDestroyed()) { if (show) win.show(); else win.hide(); }
	}

	return { start, stop, info, replaceToken, setVisible, running: () => Boolean(api) };
}

module.exports = { createAgentPlay };
