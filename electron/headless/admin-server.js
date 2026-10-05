'use strict';
//
// The admin page of a headless app: Settings, in a browser.
//
// It serves the app's own src/settings.html with one script in front of it
// (src/admin-shim.js), which gives the page the same `window.__ELECTRON__`
// bridge the Settings window has, over HTTP. Every call lands on the same
// handlers in main.js, through the allowlist main.js passes as `invoke`.
//
// Who may use it. Settings can install code (mods), restore backups over
// every character and read the database, so it is the host's alone:
//
//   - A token, made fresh at every start and printed once, opens it:
//     /settings?token=<token>. That swaps the token for a session cookie
//     (HttpOnly, SameSite=Strict) and redirects, so the token leaves the
//     address bar and the browser history. Scripts can send
//     `Authorization: Bearer <token>` instead.
//   - Every POST must carry `X-RO-Admin: 1`. A page on another site can
//     make a browser send the cookie with a form, but not with a custom
//     header, so it cannot call anything.
//   - The Host header must be one this server answers to. Without that, a
//     site could point a name of its own at 127.0.0.1 and talk to it from
//     the victim's browser (DNS rebinding).
//
// It listens on 127.0.0.1 unless told otherwise. Reaching it from another
// machine is meant to go through an SSH tunnel; listening wider is allowed,
// but this is plain HTTP and the token crosses the network as it is typed.
//

const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');

/** The pages it serves: Settings, and Setup for where the client's files are. */
const PAGES = { '/': 'settings.html', '/settings': 'settings.html', '/setup': 'setup.html' };

/** The files of src/ the pages load, and what they are. */
const ASSETS = {
	'theme.css': 'text/css; charset=utf-8',
	'mods-state.js': 'text/javascript; charset=utf-8',
	'accounts-settings.js': 'text/javascript; charset=utf-8',
	'admin-shim.js': 'text/javascript; charset=utf-8',
};

/** The largest body accepted: a mod archive, or a backup to restore. */
const UPLOAD_LIMIT = 1024 * 1024 * 1024;
const JSON_LIMIT = 4 * 1024 * 1024;

function token() {
	return crypto.randomBytes(24).toString('base64url');
}

function same(a, b) {
	const x = Buffer.from(String(a));
	const y = Buffer.from(String(b));
	return x.length === y.length && crypto.timingSafeEqual(x, y);
}

function cookies(req) {
	const out = {};
	for (const part of String(req.headers.cookie || '').split(';')) {
		const i = part.indexOf('=');
		if (i > 0) out[part.slice(0, i).trim()] = part.slice(i + 1).trim();
	}
	return out;
}

function send(res, status, type, body, headers = {}) {
	res.writeHead(status, {
		'Content-Type': type,
		'Cache-Control': 'no-store',
		'X-Content-Type-Options': 'nosniff',
		'X-Frame-Options': 'DENY',
		'Referrer-Policy': 'no-referrer',
		...headers,
	});
	res.end(body);
}

function json(res, status, value) {
	send(res, status, 'application/json; charset=utf-8', JSON.stringify(value));
}

function readBody(req, limit) {
	return new Promise((resolve, reject) => {
		const chunks = [];
		let size = 0;
		req.on('data', c => {
			size += c.length;
			if (size > limit) {
				reject(Object.assign(new Error('too large'), { status: 413 }));
				req.destroy();
				return;
			}
			chunks.push(c);
		});
		req.on('end', () => resolve(Buffer.concat(chunks)));
		req.on('error', reject);
	});
}

/**
 * Start the admin server.
 *
 * @param {object} o
 * @param {string} o.host address to listen on (127.0.0.1 unless the host chose wider)
 * @param {number} o.port
 * @param {string} o.srcDir the app's src/ (settings.html and its assets)
 * @param {(name: string, args: object) => Promise<any>} o.invoke a handler, by name, through main.js's allowlist
 * @param {import('./remote-dialogs').RemoteDialogs} o.dialogs
 * @param {() => object} o.info what the page is told about the app (game address and so on)
 * @param {string} [o.uploadDir] where uploads go; a fresh temporary folder by default
 * @param {(line: string) => void} [o.log]
 * @returns {Promise<{ url: string, token: string, port: number, close: () => Promise<void> }>}
 */
async function start(o) {
	const log = o.log || (() => {});
	const secret = o.token || token();
	const sessions = new Set();
	const uploadDir = o.uploadDir || fs.mkdtempSync(path.join(os.tmpdir(), 'ro-admin-upload-'));
	let port = o.port;

	// The names a request may arrive under: the address it listens on, and
	// loopback's names when that is what it listens on.
	const hosts = () => {
		const names = new Set([`${o.host}:${port}`]);
		if (o.host === '127.0.0.1' || o.host === 'localhost' || o.host === '0.0.0.0') {
			names.add(`127.0.0.1:${port}`);
			names.add(`localhost:${port}`);
		}
		if (o.host === '0.0.0.0') {
			for (const list of Object.values(os.networkInterfaces())) {
				for (const a of list || []) if (a.family === 'IPv4') names.add(`${a.address}:${port}`);
			}
		}
		for (const extra of o.extraHosts || []) names.add(`${extra}:${port}`);
		return names;
	};

	const authorized = req => {
		const bearer = /^Bearer\s+(.+)$/i.exec(String(req.headers.authorization || ''));
		if (bearer && same(bearer[1], secret)) return true;
		const sid = cookies(req).ro_admin;
		return !!sid && sessions.has(sid);
	};

	const page = file => {
		const html = fs.readFileSync(path.join(o.srcDir, file), 'utf8');
		// Before the page's first script, so the bridge exists when it runs.
		const i = html.indexOf('<script');
		const shim = '<script src="admin-shim.js"></script>\n';
		return i < 0 ? html + shim : html.slice(0, i) + shim + html.slice(i);
	};

	const server = http.createServer(async (req, res) => {
		try {
			const url = new URL(req.url, 'http://admin.invalid');
			if (!hosts().has(String(req.headers.host || ''))) {
				return send(res, 421, 'text/plain; charset=utf-8', 'This address is not served here.');
			}

			// The token, swapped for a session.
			if (req.method === 'GET' && url.pathname === '/settings' && url.searchParams.has('token')) {
				if (!same(url.searchParams.get('token'), secret)) {
					log('headless admin: refused a sign-in with a wrong token');
					return send(res, 403, 'text/plain; charset=utf-8', 'That token is not the one this app printed when it started.');
				}
				const sid = token();
				sessions.add(sid);
				log('headless admin: signed in');
				return send(res, 302, 'text/plain; charset=utf-8', '', {
					'Set-Cookie': `ro_admin=${sid}; HttpOnly; SameSite=Strict; Path=/`,
					Location: '/settings',
				});
			}

			if (!authorized(req)) {
				return send(res, 401, 'text/plain; charset=utf-8',
					'Open the address the app printed when it started: /settings?token=...');
			}

			if (req.method === 'GET') {
				if (Object.prototype.hasOwnProperty.call(PAGES, url.pathname)) {
					return send(res, 200, 'text/html; charset=utf-8', page(PAGES[url.pathname]));
				}
				const name = url.pathname.replace(/^\//, '');
				if (Object.prototype.hasOwnProperty.call(ASSETS, name)) {
					return send(res, 200, ASSETS[name], fs.readFileSync(path.join(o.srcDir, name)));
				}
				if (url.pathname === '/admin/api/prompts') return json(res, 200, o.dialogs.pending());
				if (url.pathname === '/admin/api/info') return json(res, 200, o.info ? o.info() : {});
				return send(res, 404, 'text/plain; charset=utf-8', 'Not found');
			}

			if (req.method !== 'POST') return send(res, 405, 'text/plain; charset=utf-8', 'Method not allowed');
			if (req.headers['x-ro-admin'] !== '1') {
				return send(res, 403, 'text/plain; charset=utf-8', 'Missing the X-RO-Admin header.');
			}

			if (url.pathname === '/admin/api/upload') {
				// A file for a question the page is answering: a mod archive, or a
				// backup. Kept under its own name in a folder of its own, so the
				// handler that receives the path sees the name the host chose.
				const name = path.basename(String(url.searchParams.get('name') || 'upload')).replace(/[^\w.\- ]/g, '_') || 'upload';
				const body = await readBody(req, UPLOAD_LIMIT);
				const dir = fs.mkdtempSync(path.join(uploadDir, 'u-'));
				const dest = path.join(dir, name);
				fs.writeFileSync(dest, body);
				log(`headless admin: received ${name} (${Math.round(body.length / 1024)} KB)`);
				return json(res, 200, { path: dest });
			}

			const body = JSON.parse((await readBody(req, JSON_LIMIT)).toString('utf8') || '{}');
			if (url.pathname === '/admin/api/invoke') {
				try {
					const value = await o.invoke(String(body.name || ''), body.args || {});
					return json(res, 200, { ok: true, value: value === undefined ? null : value });
				} catch (e) {
					return json(res, 200, { ok: false, error: (e && e.message) || String(e) });
				}
			}
			if (url.pathname === '/admin/api/answer') {
				return json(res, 200, { ok: o.dialogs.answer(body.id, body.value) });
			}
			return send(res, 404, 'text/plain; charset=utf-8', 'Not found');
		} catch (e) {
			const status = (e && e.status) || 500;
			log(`headless admin: ${req.method} ${req.url} failed: ${(e && e.message) || e}`);
			if (!res.headersSent) send(res, status, 'text/plain; charset=utf-8', status === 413 ? 'Too large' : 'Error');
		}
	});

	await new Promise((resolve, reject) => {
		server.once('error', reject);
		server.listen(port, o.host, resolve);
	});
	port = server.address().port;
	const shown = o.host === '0.0.0.0' ? '127.0.0.1' : o.host;
	return {
		url: `http://${shown}:${port}/settings?token=${secret}`,
		token: secret,
		port,
		close: () => new Promise(resolve => server.close(() => resolve())),
	};
}

module.exports = { start };
