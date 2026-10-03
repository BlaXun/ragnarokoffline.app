// The Autoloot window. Everything it shows and changes goes through
// api.server.request('modaloot', ...), answered by npc/autoloot.txt, which
// runs @autoloot, @autoloottype and @autolootitem for the player.

// The item types @autoloottype takes, by rAthena's IT_* number.
const TYPES = [
    [6, 'Cards'], [0, 'Healing'], [2, 'Usable'], [3, 'Etc'], [4, 'Armor'],
    [5, 'Weapons'], [10, 'Ammo'], [7, 'Pet eggs'], [8, 'Pet armor'],
];

const STYLE = `
:host, .wrap { font: 12px Tahoma, sans-serif; color: #273256; }
.wrap { display: flex; flex-direction: column; height: 100%; overflow: auto; }
section { padding: 6px 8px; border-bottom: 1px solid #e3e7f2; }
h4 { margin: 0 0 4px; font-size: 12px; }
.line { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
input[type=number] { width: 64px; font: inherit; padding: 2px 4px; }
input[type=text] { flex: 1; min-width: 0; font: inherit; padding: 3px 5px; border: 1px solid #aab4cf; border-radius: 3px; }
button { font: inherit; padding: 2px 8px; cursor: pointer; }
.types { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px 8px; }
.note { color: #889; font-size: 11px; margin-top: 3px; }
.row { display: flex; align-items: center; gap: 6px; padding: 2px 4px; border-radius: 3px; }
.row:hover { background: #eef2fc; }
.row img { width: 24px; height: 24px; image-rendering: pixelated; }
.row small { color: #889; margin-left: auto; white-space: nowrap; }
.row .x { padding: 0 6px; }
.pick { cursor: pointer; }
.yes { color: #2a7a2a; font-weight: bold; }
.no { color: #aaa; }
.empty { color: #889; padding: 4px; }
.error { color: #a33; }
.results { max-height: 140px; overflow: auto; }
`;

const escape = text => String(text).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const percent = rate => `${(rate / 100).toFixed(2)}%`;

/** The state line from npc/autoloot.txt, or null if it is not one. */
export function parseState(line) {
    const fields = String(line || '').split('|');
    if (fields.length < 5 || fields[0] === '') return null;
    const [rate, types, limit, adjust, items] = fields;
    return {
        rate: Number(rate), types: Number(types), limit: Number(limit), adjust: Number(adjust) !== 0,
        items: items.split(',').filter(Boolean).map(Number),
    };
}

/** A monster line from npc/autoloot.txt, or null for "no such monster". */
export function parseMonster(line) {
    const fields = String(line || '').split('|');
    if (fields.length < 3 || !fields[0]) return null;
    return {
        id: Number(fields[0]), name: fields[1],
        drops: fields[2].split(',').filter(Boolean).map(entry => {
            const [item, base, rate, type] = entry.split(':').map(Number);
            return { item, base, rate, type };
        }),
    };
}

/** Would these settings pick this drop up? Mirrors mob_item_drop in rAthena. */
export function loots(state, drop) {
    const compared = state.adjust ? drop.rate : drop.base;
    return (state.rate > 0 && compared <= state.rate)
        || (state.types & (1 << drop.type)) !== 0
        || state.items.includes(drop.item);
}

export default function init(parameters, api) {
    if (api?.version !== 1) throw new Error('autoloot requires client API 1');
    const win = api.ui.window({ id: 'autoloot', title: 'Autoloot', width: 380, height: 520 });
    const body = win.body;
    body.innerHTML = `<style>${STYLE}</style><div class="wrap">
        <section>
            <h4>By rarity</h4>
            <div class="line">
                <label><input type="checkbox" data-rarity> Loot drops at or below</label>
                <input type="number" data-rate min="0.01" max="100" step="0.01" value="1"> %
                <button data-set-rate>Set</button>
            </div>
            <div class="note" data-rate-note></div>
        </section>
        <section>
            <h4>By item type</h4>
            <div class="types">${TYPES.map(([bit, label]) => `<label><input type="checkbox" data-type="${bit}"> ${label}</label>`).join('')}</div>
        </section>
        <section>
            <h4>These items <small data-count></small></h4>
            <div data-items></div>
            <form class="line" data-search><input type="text" placeholder="Add an item: name or id" autocomplete="off"><button>Find</button></form>
            <div class="results" data-results></div>
        </section>
        <section>
            <h4>Check a monster</h4>
            <form class="line" data-mob><input type="text" placeholder="e.g. Poring or 1002" autocomplete="off"><button>Check</button></form>
            <div data-drops></div>
        </section>
        <section class="line">
            <button data-off>Turn everything off</button>
            <span class="error" data-error></span>
        </section>
    </div>`;
    const $ = selector => body.querySelector(selector);
    const rarity = $('[data-rarity]'), rateInput = $('[data-rate]'), errorLine = $('[data-error]');
    const searchInput = $('[data-search] input'), mobInput = $('[data-mob] input');
    let state = null;
    let monster = null;

    const icon = async (img, id) => { const url = await api.items.icon(id); if (url) img.src = url; };
    const itemName = id => api.items.get(id)?.name || `#${id}`;
    const icons = root => root.querySelectorAll('img[data-icon]').forEach(img => icon(img, Number(img.dataset.icon)));

    async function ask(text) {
        errorLine.textContent = '';
        try {
            const answer = await api.server.request('modaloot', text);
            if (text.startsWith('mob ')) return answer;
            const next = parseState(answer);
            if (!next) throw new Error('the server sent an answer this window does not understand');
            state = next;
            render();
            return answer;
        } catch (error) {
            errorLine.textContent = String(error.message || error);
            return null;
        }
    }

    function render() {
        if (!state) return;
        rarity.checked = state.rate > 0;
        if (state.rate > 0 && document.activeElement !== rateInput) rateInput.value = (state.rate / 100).toFixed(2);
        $('[data-rate-note]').textContent = state.adjust
            ? 'Compared with your own chance: the server\'s drop rates and your bonuses count.'
            : 'Compared with the monster\'s base rate, before the server\'s drop rates and your bonuses.';
        body.querySelectorAll('[data-type]').forEach(box => { box.checked = (state.types & (1 << Number(box.dataset.type))) !== 0; });
        $('[data-count]').textContent = `(${state.items.length}/${state.limit})`;
        const list = $('[data-items]');
        list.innerHTML = state.items.length
            ? state.items.map(id => `<div class="row"><img data-icon="${id}"><span>${escape(itemName(id))}</span><small>#${id}</small><button class="x" data-remove="${id}" title="Stop looting">×</button></div>`).join('')
            : '<div class="empty">No items yet.</div>';
        icons(list);
        list.querySelectorAll('[data-remove]').forEach(button => button.addEventListener('click', () => ask(`remove ${button.dataset.remove}`)));
        if (monster) renderMonster();
    }

    function renderMonster() {
        const drops = $('[data-drops]');
        if (!monster) { drops.innerHTML = '<div class="empty">No such monster, or it drops nothing.</div>'; return; }
        drops.innerHTML = `<div class="note">${escape(monster.name)}: base rate / your chance</div>` + monster.drops.map(drop => {
            const yes = state && loots(state, drop);
            return `<div class="row"><img data-icon="${drop.item}"><span>${escape(itemName(drop.item))}</span>
                <small>${percent(drop.base)} / ${drop.rate < 0 ? '–' : percent(drop.rate)}</small>
                <span class="${yes ? 'yes' : 'no'}" title="${yes ? 'Looted' : 'Not looted'}">${yes ? '✓' : '–'}</span></div>`;
        }).join('');
        icons(drops);
    }

    function setRate() {
        const value = Math.round(Number(rateInput.value) * 100);
        if (!Number.isFinite(value) || value < 1 || value > 10000) {
            errorLine.textContent = 'The rarity is a percent from 0.01 to 100.';
            return;
        }
        ask(`rate ${value}`);
    }

    rarity.addEventListener('change', () => { if (rarity.checked) setRate(); else ask('rate 0'); });
    $('[data-set-rate]').addEventListener('click', setRate);
    body.querySelectorAll('[data-type]').forEach(box => box.addEventListener('change', () => ask(`type ${box.checked ? '+' : '-'}${box.dataset.type}`)));
    $('[data-off]').addEventListener('click', () => ask('off'));

    $('[data-search]').addEventListener('submit', event => {
        event.preventDefault();
        const results = $('[data-results]');
        const query = searchInput.value.trim();
        const items = query ? api.items.search(query, 40) : [];
        results.innerHTML = items.length
            ? items.map(item => `<div class="row pick" data-add="${item.id}"><img data-icon="${item.id}"><span>${escape(item.name)}</span><small>#${item.id}</small></div>`).join('')
            : (query ? '<div class="empty">Nothing found.</div>' : '');
        icons(results);
        results.querySelectorAll('[data-add]').forEach(row => row.addEventListener('click', () => {
            if (state && state.items.length >= state.limit) {
                errorLine.textContent = `The list holds ${state.limit} items. Remove one first.`;
                return;
            }
            results.innerHTML = '';
            searchInput.value = '';
            ask(`add ${row.dataset.add}`);
        }));
    });

    $('[data-mob]').addEventListener('submit', async event => {
        event.preventDefault();
        const query = mobInput.value.trim();
        if (!query) return;
        $('[data-drops]').textContent = 'Asking the server…';
        const answer = await ask(`mob ${query}`);
        if (answer === null) { $('[data-drops]').textContent = ''; return; }
        monster = parseMonster(answer);
        renderMonster();
    });

    function toggle() {
        win.toggle();
        if (win.isOpen()) ask('get');
    }

    // Open with Alt+O.
    const onKey = event => { if (event.altKey && event.code === 'KeyO') { event.preventDefault(); toggle(); } };
    addEventListener('keydown', onKey, true);
    api.cleanup(() => removeEventListener('keydown', onKey, true));
}
