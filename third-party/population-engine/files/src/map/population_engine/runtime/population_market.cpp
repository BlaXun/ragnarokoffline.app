// Copyright (c) rAthena Dev Teams - Licensed under GNU GPL
// For more information, see LICENCE in the main folder
//
// RAGNAROKMAC: a dynamic market.
//
// Every item has a price index, 1.00 at its baseline (a mod's price table).
// Trades move it: a player buying from a fake stall pushes it up, selling to
// a fake buyer pushes it down, and a customer or seller at a player's own
// stall pulls it toward the price they dealt at. How far one trade moves it
// depends on how much of the item normally changes hands in a day, so 500
// Jellopy barely register and three Angeling Cards do. A move spills over to
// related items (population_market.yml groups), and optional news events push
// a group for some days. Everything drifts back to the baseline with a
// half-life, worked out from timestamps whenever a price is read, so the time
// the server was off counts too. The index stays within 0.5-2.0.
//
// Fake stalls price their stock at the index when they open, fake buyers
// offer at it, and the customers of players' stalls (population_customers)
// judge prices against it. A board NPC reads the top movers and the news from
// $@pop_board_* variables written here once a minute; shells that sell a
// mover say so now and then (trend shouts, at most one per map in ten
// minutes). @vendorinfo market shows it all.
//
// Off unless a mod switches it on, through temporary server variables its
// settings NPC sets at start:
//
//   $@pop_market               1 = on
//   $@pop_market_strength      how hard trades move prices, percent (100)
//   $@pop_market_halflife      hours for half of a move to fade (72)
//   $@pop_market_news          1 = news events
//   $@pop_customers_table$     the price table the baseline comes from
//
// State is the engine's own, in permanent server variables: $pop_mk_* (items
// that moved) and $pop_mn_* (news). Included into population_engine.cpp after
// the mod vendor code it uses.

#include <cmath>
#include <ctime>

/// What the mod switched on, read from the server variables.
struct PopMarketSettings {
	bool on = false, news = false;
	double strength = 1.0;      ///< 1.0 = 100 %
	double half_life = 72 * 3600.0;
	std::string table;          ///< "prontera-vendors/"
};

static int64 pop_market_reg(const char* name, int32 idx = 0) {
	return mapreg_readreg(reference_uid(add_str(name), idx));
}

static std::string pop_market_regstr(const char* name, int32 idx = 0) {
	const char* s = mapreg_readregstr(reference_uid(add_str(name), idx));
	return s != nullptr ? s : "";
}

static void pop_market_setreg(const char* name, int32 idx, int64 v) {
	mapreg_setreg(reference_uid(add_str(name), idx), v);
}

static void pop_market_setregstr(const char* name, int32 idx, const std::string& v) {
	mapreg_setregstr(reference_uid(add_str(name), idx), v.empty() ? nullptr : v.c_str());
}

static PopMarketSettings pop_market_settings() {
	PopMarketSettings ms;
	ms.table = pop_market_regstr("$@pop_customers_table$");
	if (!ms.table.empty() && ms.table.back() != '/')
		ms.table += '/';
	ms.on = !ms.table.empty() && pop_market_reg("$@pop_market") != 0;
	ms.news = pop_market_reg("$@pop_market_news") != 0;
	if (const int64 v = pop_market_reg("$@pop_market_strength"); v > 0)
		ms.strength = std::min<int64>(v, 1000) / 100.0;
	if (const int64 v = pop_market_reg("$@pop_market_halflife"); v > 0)
		ms.half_life = std::min<int64>(v, 24 * 365) * 3600.0;
	return ms;
}

static const double POP_MARKET_LN_MIN = std::log(0.5);
static const double POP_MARKET_LN_MAX = std::log(2.0);

/// An item that moved: its log index from trades and when that was true.
struct PopMarketItem {
	double ln = 0;
	time_t at = 0;
	std::string why; ///< the last thing that moved it, for @vendorinfo market
};

/// A news event running (or fading): which, its rolled changes, and when.
struct PopMarketNews {
	std::string key;
	std::vector<int> change; ///< percent per effect, rolled at start
	time_t start = 0, end = 0;
};

static std::unordered_map<t_itemid, PopMarketItem> g_pop_market;
static std::vector<PopMarketNews> g_pop_market_news;
static std::unordered_map<std::string, time_t> g_pop_market_news_used; ///< event key -> last start
static std::unordered_map<t_itemid, double> g_pop_market_event_ln;     ///< per pass: news' share of each item's log index
static bool g_pop_market_loaded = false;
static bool g_pop_market_dirty = false;
static std::unordered_map<int16, t_tick> g_pop_market_last_trend;      ///< per map: last trend shout
static constexpr t_tick POP_MARKET_TREND_GAP = 10 * 60 * 1000;
static constexpr time_t POP_MARKET_NEWS_REPEAT = 28 * 86400;
static constexpr size_t POP_MARKET_NEWS_MAX = 2;

static const PopulationMarketEvent* pop_market_event(const std::string& key) {
	for (const PopulationMarketEvent& e : population_market_db().events())
		if (e.key == key)
			return &e;
	return nullptr;
}

static void pop_market_load() {
	if (g_pop_market_loaded)
		return;
	g_pop_market_loaded = true;
	const int64 n = pop_market_reg("$pop_mk_n");
	for (int32 i = 0; i < n; ++i) {
		const t_itemid id = static_cast<t_itemid>(pop_market_reg("$pop_mk_id", i));
		if (id == 0)
			continue;
		PopMarketItem it;
		it.ln = pop_market_reg("$pop_mk_v", i) / 1e6;
		it.at = static_cast<time_t>(pop_market_reg("$pop_mk_t", i));
		g_pop_market[id] = it;
	}
	const int64 nn = pop_market_reg("$pop_mn_n");
	for (int32 i = 0; i < nn; ++i) {
		PopMarketNews news;
		news.key = pop_market_regstr("$pop_mn_key$", i);
		news.start = static_cast<time_t>(pop_market_reg("$pop_mn_start", i));
		news.end = static_cast<time_t>(pop_market_reg("$pop_mn_end", i));
		const std::string c = pop_market_regstr("$pop_mn_c$", i);
		for (size_t p = 0; p < c.size();) {
			const size_t q = c.find(',', p);
			news.change.push_back(atoi(c.substr(p, q == std::string::npos ? std::string::npos : q - p).c_str()));
			if (q == std::string::npos) break;
			p = q + 1;
		}
		if (!news.key.empty())
			g_pop_market_news.push_back(news);
	}
	const int64 nu = pop_market_reg("$pop_mn_used_n");
	for (int32 i = 0; i < nu; ++i) {
		const std::string key = pop_market_regstr("$pop_mn_used$", i);
		if (!key.empty())
			g_pop_market_news_used[key] = static_cast<time_t>(pop_market_reg("$pop_mn_usedt", i));
	}
}

static void pop_market_save() {
	if (!g_pop_market_dirty)
		return;
	g_pop_market_dirty = false;
	const int64 old_n = pop_market_reg("$pop_mk_n");
	int32 i = 0;
	for (const auto& kv : g_pop_market) {
		pop_market_setreg("$pop_mk_id", i, kv.first);
		pop_market_setreg("$pop_mk_v", i, static_cast<int64>(std::llround(kv.second.ln * 1e6)));
		pop_market_setreg("$pop_mk_t", i, kv.second.at);
		++i;
	}
	for (int32 j = i; j < old_n; ++j) {
		pop_market_setreg("$pop_mk_id", j, 0);
		pop_market_setreg("$pop_mk_v", j, 0);
		pop_market_setreg("$pop_mk_t", j, 0);
	}
	pop_market_setreg("$pop_mk_n", 0, i);

	const int64 old_nn = pop_market_reg("$pop_mn_n");
	int32 k = 0;
	for (const PopMarketNews& news : g_pop_market_news) {
		std::string c;
		for (size_t e = 0; e < news.change.size(); ++e)
			c += (e ? "," : "") + std::to_string(news.change[e]);
		pop_market_setregstr("$pop_mn_key$", k, news.key);
		pop_market_setreg("$pop_mn_start", k, news.start);
		pop_market_setreg("$pop_mn_end", k, news.end);
		pop_market_setregstr("$pop_mn_c$", k, c);
		++k;
	}
	for (int32 j = k; j < old_nn; ++j) {
		pop_market_setregstr("$pop_mn_key$", j, "");
		pop_market_setreg("$pop_mn_start", j, 0);
		pop_market_setreg("$pop_mn_end", j, 0);
		pop_market_setregstr("$pop_mn_c$", j, "");
	}
	pop_market_setreg("$pop_mn_n", 0, k);

	const int64 old_nu = pop_market_reg("$pop_mn_used_n");
	int32 u = 0;
	for (const auto& kv : g_pop_market_news_used) {
		pop_market_setregstr("$pop_mn_used$", u, kv.first);
		pop_market_setreg("$pop_mn_usedt", u, kv.second);
		++u;
	}
	for (int32 j = u; j < old_nu; ++j) {
		pop_market_setregstr("$pop_mn_used$", j, "");
		pop_market_setreg("$pop_mn_usedt", j, 0);
	}
	pop_market_setreg("$pop_mn_used_n", 0, u);
}

/// An item's log index from trades now: what it was, faded by the time since.
static double pop_market_trade_ln(const PopMarketItem& it, time_t now, double half_life) {
	if (it.at == 0 || now <= it.at)
		return it.ln;
	return it.ln * std::pow(0.5, (now - it.at) / half_life);
}

/// How much of a news event still holds: all of it while it runs, then fading.
static double pop_market_news_weight(const PopMarketNews& news, time_t now, double half_life) {
	if (now < news.end)
		return 1.0;
	return std::pow(0.5, (now - news.end) / half_life);
}

/// News' share of every item's log index, for this pass.
static void pop_market_event_shares(time_t now, double half_life) {
	g_pop_market_event_ln.clear();
	for (const PopMarketNews& news : g_pop_market_news) {
		const PopulationMarketEvent* e = pop_market_event(news.key);
		if (e == nullptr)
			continue;
		const double w = pop_market_news_weight(news, now, half_life);
		for (size_t f = 0; f < e->effects.size() && f < news.change.size(); ++f) {
			const double ln = w * std::log(1.0 + news.change[f] / 100.0);
			for (t_itemid id : e->effects[f].items)
				g_pop_market_event_ln[id] += ln;
		}
	}
}

/// An item's price index now (1.0 = baseline), or 1.0 when the market is off.
static double population_market_factor(t_itemid id) {
	static PopMarketSettings ms;
	static time_t read_at = 0;
	const time_t now = time(nullptr);
	if (now != read_at) { // the settings, at most once a second
		ms = pop_market_settings();
		read_at = now;
	}
	if (!ms.on)
		return 1.0;
	pop_market_load();
	double ln = 0;
	auto it = g_pop_market.find(id);
	if (it != g_pop_market.end())
		ln += pop_market_trade_ln(it->second, now, ms.half_life);
	auto ev = g_pop_market_event_ln.find(id);
	if (ev != g_pop_market_event_ln.end())
		ln += ev->second;
	return std::exp(std::max(POP_MARKET_LN_MIN, std::min(POP_MARKET_LN_MAX, ln)));
}

/// An item's baseline price: the middle of its range in the price table at
/// the mod's price level, else what an NPC charges.
static double pop_market_baseline(const PopMarketSettings& ms, t_itemid id, PopMarketRow* row_out = nullptr) {
	std::shared_ptr<item_data> data = item_db.find(id);
	double price = data ? std::max<double>({ 1.0, static_cast<double>(data->value_buy), static_cast<double>(data->value_sell) * 2 }) : 1.0;
	auto t = g_pop_market_tables.find(ms.table);
	if (t != g_pop_market_tables.end()) {
		auto r = t->second.find(id);
		if (r != t->second.end()) {
			if (row_out)
				*row_out = r->second;
			if (r->second.lo > 0)
				price = (static_cast<double>(r->second.lo) + r->second.hi) / 2;
		}
	}
	const PopModVendorSettings* st = pop_mod_vendor_settings_for_key(ms.table);
	if (st && st->price_pct > 0)
		price = price * st->price_pct / 100;
	return price;
}

/// How many of an item change hands on a normal day: its customers and
/// sellers a day (the price table), times what each deals in (cheap loot by
/// the hundred, dear things one at a time).
static double pop_market_volume(const PopMarketSettings& ms, t_itemid id) {
	PopMarketRow row;
	const double price = pop_market_baseline(ms, id, &row);
	const double deals = std::max(1.0, ((row.buyers_day > 0 ? row.buyers_day : 4) + (row.sellers_day > 0 ? row.sellers_day : 4)) / 2.0);
	const double each = price < 1000 ? 100 : price < 20000 ? 3 : price < 200000 ? 1.5 : 1;
	return deals * each;
}

/// Move an item's log index by delta (and its groups' by their share).
static void pop_market_move(const PopMarketSettings& ms, t_itemid id, double delta, const std::string& why, time_t now) {
	auto apply = [&](t_itemid target, double d, const std::string& w) {
		PopMarketItem& it = g_pop_market[target];
		it.ln = std::max(POP_MARKET_LN_MIN, std::min(POP_MARKET_LN_MAX, pop_market_trade_ln(it, now, ms.half_life) + d));
		it.at = now;
		it.why = w;
	};
	apply(id, delta, why);
	if (const std::vector<size_t>* gs = population_market_db().groups_of(id)) {
		std::shared_ptr<item_data> data = item_db.find(id);
		const std::string by = "with " + (data ? data->ename : std::string("?"));
		for (size_t g : *gs) {
			const PopulationMarketGroup& group = population_market_db().groups()[g];
			for (t_itemid other : group.items)
				if (other != id)
					apply(other, delta * group.share_pct / 100.0, by);
		}
	}
	g_pop_market_dirty = true;
}

/// A trade on the market. kind: 0 a player bought from a fake stall, 1 a
/// player sold to a fake buyer, 2 a customer bought from a player's stall,
/// 3 a seller sold into a player's buying store. Public: the vending and
/// buying store hooks (patch 0026) call it for 0 and 1.
void population_engine_market_trade(uint32_t id, int amount, uint32_t price, int kind) {
	const PopMarketSettings ms = pop_market_settings();
	if (!ms.on || id == 0 || amount <= 0)
		return;
	pop_market_load();
	const time_t now = time(nullptr);
	// One normal day's volume moves a price by about 40 % at strength 100:
	// 30 Elunium about 5 %, 3 Angeling Cards about 12 %.
	const double share = ms.strength * 0.4 * amount / pop_market_volume(ms, id);
	double delta = 0;
	const char* what = "";
	switch (kind) {
		case 0: delta = share; what = "bought from a stall"; break;
		case 1: delta = -share; what = "sold to a buyer"; break;
		default: {
			// Toward the price it went at: a sale under market pulls down,
			// over market up (and never past it).
			const double market = pop_market_baseline(ms, id) * population_market_factor(id);
			const double r = std::log(std::max(1.0, static_cast<double>(price)) / std::max(1.0, market));
			delta = std::min(1.0, share) * r;
			what = kind == 2 ? "a customer bought" : "a seller sold";
		}
	}
	delta = std::max(-0.25, std::min(0.25, delta));
	if (std::fabs(delta) < 1e-6)
		return;
	char why[96];
	safesnprintf(why, sizeof(why), "%s: %d at %s", what, amount, pop_price_short(price).c_str());
	pop_market_move(ms, id, delta, why, now);
}

/// Start a news event now (its changes rolled), or false if it cannot run.
static bool pop_market_start_news(const std::string& key, time_t now) {
	const PopulationMarketEvent* e = pop_market_event(key);
	if (e == nullptr)
		return false;
	for (const PopMarketNews& n : g_pop_market_news)
		if (n.key == key && now < n.end)
			return false;
	PopMarketNews news;
	news.key = key;
	news.start = now;
	news.end = now + static_cast<time_t>(e->days) * 86400;
	for (const PopulationMarketEffect& f : e->effects)
		news.change.push_back(f.change_min + static_cast<int>(rnd() % static_cast<uint32_t>(f.change_max - f.change_min + 1)));
	g_pop_market_news.erase(std::remove_if(g_pop_market_news.begin(), g_pop_market_news.end(),
		[&](const PopMarketNews& n) { return n.key == key; }), g_pop_market_news.end());
	g_pop_market_news.push_back(news);
	g_pop_market_news_used[key] = now;
	g_pop_market_dirty = true;
	ShowInfo("Population engine: market news '%s' for %d day(s).\n", key.c_str(), e->days);
	return true;
}

/// The market board's lines: the top five risers and fallers and the news.
static void pop_market_board(const PopMarketSettings& ms, time_t now) {
	std::vector<std::pair<double, t_itemid>> movers;
	std::unordered_set<t_itemid> seen;
	auto consider = [&](t_itemid id) {
		if (!seen.insert(id).second)
			return;
		const double f = population_market_factor(id);
		if (std::fabs(f - 1.0) >= 0.03)
			movers.emplace_back(f, id);
	};
	for (const auto& kv : g_pop_market)
		consider(kv.first);
	for (const auto& kv : g_pop_market_event_ln)
		consider(kv.first);
	std::sort(movers.begin(), movers.end());
	auto line = [](double f, t_itemid id) {
		std::shared_ptr<item_data> data = item_db.find(id);
		char buf[96];
		safesnprintf(buf, sizeof(buf), "%s %+d%%", data ? data->ename.c_str() : "?", static_cast<int>(std::lround((f - 1.0) * 100)));
		return std::string(buf);
	};
	int up = 0, down = 0;
	for (auto it = movers.rbegin(); it != movers.rend() && up < 5; ++it)
		if (it->first > 1.0)
			pop_market_setregstr("$@pop_board_up$", up++, line(it->first, it->second));
	for (auto it = movers.begin(); it != movers.end() && down < 5; ++it)
		if (it->first < 1.0)
			pop_market_setregstr("$@pop_board_down$", down++, line(it->first, it->second));
	for (int i = up; i < 5; ++i) pop_market_setregstr("$@pop_board_up$", i, "");
	for (int i = down; i < 5; ++i) pop_market_setregstr("$@pop_board_down$", i, "");
	int n = 0;
	for (const PopMarketNews& news : g_pop_market_news) {
		const PopulationMarketEvent* e = pop_market_event(news.key);
		if (e == nullptr || n >= 4)
			continue;
		char buf[256];
		if (now < news.end)
			safesnprintf(buf, sizeof(buf), "%s (%d more day%s)", e->text.c_str(),
				static_cast<int>((news.end - now + 86399) / 86400), (news.end - now) > 86400 ? "s" : "");
		else
			safesnprintf(buf, sizeof(buf), "%s (fading)", e->text.c_str());
		pop_market_setregstr("$@pop_board_news$", n++, buf);
	}
	for (int i = n; i < 4; ++i) pop_market_setregstr("$@pop_board_news$", i, "");
	pop_market_setreg("$@pop_board_on", 0, ms.on ? 1 : 0);
}

/// Once a minute: news' shares, new news now and then, faded entries
/// dropped, the board, and the state saved.
static void population_market_pass() {
	const PopMarketSettings ms = pop_market_settings();
	pop_market_setreg("$@pop_board_on", 0, ms.on ? 1 : 0);
	if (!ms.on)
		return;
	pop_market_load();
	const time_t now = time(nullptr);

	// Faded away: items back within 0.5 % and news down to 2 %.
	for (auto it = g_pop_market.begin(); it != g_pop_market.end();) {
		if (std::fabs(pop_market_trade_ln(it->second, now, ms.half_life)) < 0.005) {
			it = g_pop_market.erase(it);
			g_pop_market_dirty = true;
		} else {
			++it;
		}
	}
	const size_t before = g_pop_market_news.size();
	g_pop_market_news.erase(std::remove_if(g_pop_market_news.begin(), g_pop_market_news.end(),
		[&](const PopMarketNews& n) { return pop_market_news_weight(n, now, ms.half_life) < 0.02; }), g_pop_market_news.end());
	if (g_pop_market_news.size() != before)
		g_pop_market_dirty = true;

	// News: about once a week, at most two at once, none again within four weeks.
	if (ms.news && !population_market_db().events().empty() && rnd() % (7 * 1440) == 0) {
		size_t running = 0;
		for (const PopMarketNews& n : g_pop_market_news)
			if (now < n.end)
				++running;
		if (running < POP_MARKET_NEWS_MAX) {
			std::vector<std::string> free;
			for (const PopulationMarketEvent& e : population_market_db().events()) {
				auto u = g_pop_market_news_used.find(e.key);
				if (u == g_pop_market_news_used.end() || now - u->second >= POP_MARKET_NEWS_REPEAT)
					free.push_back(e.key);
			}
			if (!free.empty())
				pop_market_start_news(free[rnd() % free.size()], now);
		}
	}

	pop_market_event_shares(now, ms.half_life);
	pop_market_board(ms, now);
	pop_market_save();
}

/// A trend shout for a fake stall, now and then: an item it sells (or buys)
/// whose price moved at least 15 %, at most one per map in ten minutes.
/// False when there is nothing to say, so the stall says its usual line.
static bool population_market_trend_line(map_session_data* sd, char* out, size_t out_sz) {
	if (sd == nullptr || out == nullptr || out_sz == 0)
		return false;
	const t_tick now = gettick();
	auto last = g_pop_market_last_trend.find(sd->m);
	if (last != g_pop_market_last_trend.end() && DIFF_TICK(now, last->second) < POP_MARKET_TREND_GAP)
		return false;
	if (rnd() % 2)
		return false; // not every turn, so the street keeps its own lines
	double best = 0;
	t_itemid pick = 0;
	uint32 price = 0;
	bool buying = false;
	if (sd->state.buyingstore) {
		for (int i = 0; i < sd->buyingstore.slots; ++i) {
			const double f = population_market_factor(sd->buyingstore.items[i].nameid);
			if (f >= 1.15 && f - 1.0 > best) {
				best = f - 1.0; pick = sd->buyingstore.items[i].nameid; price = sd->buyingstore.items[i].price; buying = true;
			}
		}
	} else if (sd->state.vending) {
		for (int j = 0; j < sd->vend_num; ++j) {
			const int16 ci = sd->vending[j].index;
			if (ci < 0 || ci >= MAX_CART)
				continue;
			const t_itemid id = sd->cart.u.items_cart[ci].nameid;
			const double f = population_market_factor(id);
			if (std::fabs(f - 1.0) >= 0.15 && std::fabs(f - 1.0) > best) {
				best = std::fabs(f - 1.0); pick = id; price = sd->vending[j].value; buying = false;
			}
		}
	}
	if (pick == 0)
		return false;
	std::shared_ptr<item_data> data = item_db.find(pick);
	if (!data)
		return false;
	const double f = population_market_factor(pick);
	char zeny[32];
	population_engine_format_zeny_compact(price, zeny, sizeof(zeny));
	static const char* const down_lines[] = { "S> %s %s, cheap today!", "S> %s only %s, prices are down", "%s at %s, grab it while it's cheap" };
	static const char* const up_lines[] = { "S> %s %s, prices are up", "S> %s %s, going fast", "%s %s, everyone wants it" };
	static const char* const buy_lines[] = { "B> %s %s, paying well", "B> %s, %s ea, prices are up", "WTB %s %s, good price" };
	const char* const* set = buying ? buy_lines : f < 1.0 ? down_lines : up_lines;
	char body[CHAT_SIZE_MAX];
	safesnprintf(body, sizeof(body), set[rnd() % 3], data->ename.c_str(), zeny);
	safestrncpy(out, body, out_sz);
	g_pop_market_last_trend[sd->m] = now;
	return true;
}

/// @vendorinfo market [<item> | news [<event>] | reset]
static void population_market_info(map_session_data* sd, const std::string& arg) {
	const int fd = sd->fd;
	char buf[CHAT_SIZE_MAX];
	const PopMarketSettings ms = pop_market_settings();
	pop_market_load();
	const time_t now = time(nullptr);
	pop_market_event_shares(now, ms.half_life);
	safesnprintf(buf, sizeof(buf), "Market: %s, strength %d%%, half-life %d h, news %s, %zu item(s) moved, %zu news.",
		ms.on ? "on" : "off", static_cast<int>(std::lround(ms.strength * 100)), static_cast<int>(ms.half_life / 3600),
		ms.news ? "on" : "off", g_pop_market.size(), g_pop_market_news.size());
	clif_displaymessage(fd, buf);

	if (arg == "reset") {
		g_pop_market.clear();
		g_pop_market_news.clear();
		g_pop_market_event_ln.clear();
		g_pop_market_dirty = true;
		pop_market_save();
		clif_displaymessage(fd, "Every price is back at its baseline, and the news is cleared.");
		return;
	}
	if (arg.compare(0, 4, "news") == 0) {
		std::string key = arg.size() > 4 ? arg.substr(5) : "";
		if (!key.empty()) {
			clif_displaymessage(fd, pop_market_start_news(key, now) ? "Started." : "No such event, or it is running already.");
			if (g_pop_market_dirty) { pop_market_event_shares(now, ms.half_life); pop_market_board(ms, now); pop_market_save(); }
			return;
		}
		for (const PopulationMarketEvent& e : population_market_db().events()) {
			std::string state = "";
			for (const PopMarketNews& n : g_pop_market_news)
				if (n.key == e.key)
					state = now < n.end ? " [running]" : " [fading]";
			safesnprintf(buf, sizeof(buf), "  %s (%d days, %zu effect(s))%s", e.key.c_str(), e.days, e.effects.size(), state.c_str());
			clif_displaymessage(fd, buf);
		}
		clif_displaymessage(fd, "@vendorinfo market news <event> starts one now.");
		return;
	}
	if (!arg.empty()) {
		std::shared_ptr<item_data> data = item_db.searchname(arg.c_str());
		if (!data && std::all_of(arg.begin(), arg.end(), ::isdigit))
			data = item_db.find(static_cast<t_itemid>(strtoul(arg.c_str(), nullptr, 10)));
		if (!data) {
			clif_displaymessage(fd, "No such item (use its AegisName or id).");
			return;
		}
		const t_itemid id = data->nameid;
		const double base = pop_market_baseline(ms, id);
		const double f = population_market_factor(id);
		auto it = g_pop_market.find(id);
		const double tln = it != g_pop_market.end() ? pop_market_trade_ln(it->second, now, ms.half_life) : 0;
		auto ev = g_pop_market_event_ln.find(id);
		safesnprintf(buf, sizeof(buf), "%s: index %.2f (trades %+d%%, news %+d%%), price %s (baseline %s), normal day %.0f",
			data->ename.c_str(), f, static_cast<int>(std::lround((std::exp(tln) - 1) * 100)),
			static_cast<int>(std::lround((std::exp(ev != g_pop_market_event_ln.end() ? ev->second : 0) - 1) * 100)),
			pop_price_short(static_cast<uint32_t>(base * f)).c_str(), pop_price_short(static_cast<uint32_t>(base)).c_str(),
			pop_market_volume(ms, id));
		clif_displaymessage(fd, buf);
		if (it != g_pop_market.end()) {
			safesnprintf(buf, sizeof(buf), "  last: %s, %d min ago; half of the rest fades in %d h",
				it->second.why.empty() ? "?" : it->second.why.c_str(), static_cast<int>((now - it->second.at) / 60),
				static_cast<int>(ms.half_life / 3600));
			clif_displaymessage(fd, buf);
		}
		return;
	}
	std::vector<std::pair<double, t_itemid>> movers;
	std::unordered_set<t_itemid> seen;
	for (const auto& kv : g_pop_market)
		if (seen.insert(kv.first).second) movers.emplace_back(population_market_factor(kv.first), kv.first);
	for (const auto& kv : g_pop_market_event_ln)
		if (seen.insert(kv.first).second) movers.emplace_back(population_market_factor(kv.first), kv.first);
	std::sort(movers.begin(), movers.end(), [](const auto& a, const auto& b) { return std::fabs(a.first - 1) > std::fabs(b.first - 1); });
	size_t shown = 0;
	for (const auto& m : movers) {
		if (++shown > 15) break;
		std::shared_ptr<item_data> data = item_db.find(m.second);
		safesnprintf(buf, sizeof(buf), "  %s %.2f %s (%+d%%)", data ? data->ename.c_str() : "?", m.first,
			m.first >= 1 ? "up" : "down", static_cast<int>(std::lround((m.first - 1) * 100)));
		clif_displaymessage(fd, buf);
	}
	for (const PopMarketNews& n : g_pop_market_news) {
		safesnprintf(buf, sizeof(buf), "  news: %s, %s", n.key.c_str(), now < n.end ? "running" : "fading");
		clif_displaymessage(fd, buf);
	}
	clif_displaymessage(fd, "@vendorinfo market <item> | news [<event>] | reset");
}
