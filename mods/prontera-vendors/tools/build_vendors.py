#!/usr/bin/env python3
"""Build prontera-vendors' two YAML files from rAthena's own data.

    python3 mods/prontera-vendors/tools/build_vendors.py [--refresh-prices | --all-prices] [--reprice]

Each theme below says *what* a stall sells: a hand list, a rule over the item
database, or "whatever the monsters of these dungeons drop". The script
resolves that against vendor/rathena (renewal item, mob and spawn databases),
prices every item, and writes:

    db/population_vendors.yml      one VendorKey per theme, with its Pool
    db/population_vendor_pop.yml   one PlacementBound shell profile per theme

Prices come from tools/prices.json, a cache of iRO player-market averages
(ragnastats.com, roughly 2013-2020 data). --refresh-prices fetches any item
the cache lacks; --all-prices fetches every tradeable item (about an hour),
so rule themes rank by what players really traded. Delete an entry to fetch
it again.

Prices also go to db/population_vendor_prices/prontera-vendors.csv
(Id,Name,Min,Max), which the server reads and which wins over the YAML. A
re-run keeps every row already there, so hand edits survive; --reprice
rebuilds it from market data instead. Those averages include
refined and carded copies, so for equipment an NPC also sells, the NPC price
wins, and averages that are wildly out of line with an item's NPC value are
treated as trolling and ignored.

The output is ordinary YAML: tune it by hand if you like, but a re-run
overwrites it, so lasting changes belong in this script.
"""
import json
import os
import random
import re
import subprocess
import sys
import time

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(MOD))
RA = os.path.join(REPO, "vendor", "rathena")
PRICES = os.path.join(HERE, "prices.json")
# The price table the server reads (Id,Name,Min,Max). Rows already in it are
# kept as they are, so hand edits survive a re-run; new items are appended.
TABLE_CSV = os.path.join(MOD, "db", "population_vendor_prices", "prontera-vendors.csv")
PREFIX = "prontera-vendors/"
CANDIDATE_CAP = 80

Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

# Prontera's sidewalks: west (x=147) and east (x=164) of the main road.
AREAS = [
    {"X1": 147, "Y1": 136, "X2": 147, "Y2": 170},
    {"X1": 164, "Y1": 135, "X2": 164, "Y2": 173},
]

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_items():
    by_name, by_id = {}, {}
    for f in ("item_db_equip.yml", "item_db_usable.yml", "item_db_etc.yml"):
        body = yaml.load(open(os.path.join(RA, "db", "re", f), encoding="utf-8"), Loader=Loader).get("Body") or []
        for e in body:
            by_name[e["AegisName"].lower()] = e
            by_id[e["Id"]] = e
    return by_name, by_id


def load_mobs():
    body = yaml.load(open(os.path.join(RA, "db", "re", "mob_db.yml"), encoding="utf-8"), Loader=Loader)["Body"]
    return {m["Id"]: m for m in body}


def npc_shop_items():
    """Item ids any plain zeny `shop` NPC sells."""
    ids = set()
    for root, _, files in os.walk(os.path.join(RA, "npc")):
        for f in files:
            if not f.endswith(".txt"):
                continue
            for line in open(os.path.join(root, f), encoding="utf-8", errors="replace"):
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 4 and parts[1] == "shop":
                    for tok in parts[3].split(",")[1:]:
                        m = re.match(r"(\d+):", tok)
                        if m:
                            ids.add(int(m.group(1)))
    return ids


def mob_ref(tok):
    """A spawn line's monster, by id ("1161,...") or Aegis name ("GAN_CEANN,...")."""
    ref = tok.split(",")[0].strip()
    if ref.isdigit():
        return int(ref)
    return MOBS_BY_AEGIS.get(ref.upper())


def spawns(files):
    """(mob id, is_boss_monster) for every spawn line in npc/re/mobs/<file>
    (a bare file name means dungeons/)."""
    out = []
    for f in files:
        path = os.path.join(RA, "npc", "re", "mobs", f if "/" in f else os.path.join("dungeons", f))
        for line in open(path, encoding="utf-8", errors="replace"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 4 and parts[1].startswith(("monster", "boss_monster")):
                mid = mob_ref(parts[3])
                if mid:
                    out.append((mid, parts[1].startswith("boss_monster")))
    return out


ITEMS, ITEMS_BY_ID = load_items()
MOBS = load_mobs()
MOBS_BY_AEGIS = {m["AegisName"].upper(): i for i, m in MOBS.items()}
NPC_SOLD = npc_shop_items()
MVP_IDS = {i for i, m in MOBS.items() if m.get("MvpExp", 0) > 0}


def item(name):
    return ITEMS.get(name.lower())


def tradeable(e):
    t = e.get("Trade") or {}
    return not (t.get("NoTrade") or t.get("NoCart") or t.get("NoDrop"))


def is_equip(e):
    return e.get("Type") in ("Weapon", "Armor", "ShadowGear")


# Cards that MVPs drop are never sold: on a real server they are the
# million-zeny trophies nobody parts with on a sidewalk.
MVP_CARDS = set()
for _mid in MVP_IDS:
    for _d in MOBS[_mid].get("Drops") or []:
        _e = item(_d["Item"])
        if _e and _e.get("Type") == "Card":
            MVP_CARDS.add(_e["Id"])

# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

try:
    CACHE = json.load(open(PRICES))
except FileNotFoundError:
    CACHE = {}


def fetch(iid):
    try:
        raw = subprocess.run(["curl", "-s", "-m", "20", "-A", "Mozilla/5.0", f"https://ragnastats.com/item/{iid}"],
                             capture_output=True, timeout=30).stdout
    except subprocess.TimeoutExpired:
        return [None, 0]
    h = raw.decode("utf-8", errors="replace")
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", h))
    m = re.search(r"Average Price ([\d,]+)z", t)
    n = re.search(r"Seen (\d+) times", t)
    return [int(m.group(1).replace(",", "")) if m else None, int(n.group(1)) if n else 0]


_fetched = 0


def market(iid, refresh):
    global _fetched
    k = str(iid)
    if k not in CACHE and refresh:
        CACHE[k] = fetch(iid)
        _fetched += 1
        if _fetched % 25 == 0:
            json.dump(CACHE, open(PRICES, "w"), indent=0, sort_keys=True)
            print(f"    {_fetched} prices fetched", file=sys.stderr)
        time.sleep(0.3)
    return CACHE.get(k, [None, 0])


def price(e, refresh):
    """A believable player price, or None to leave the item out."""
    # A price in the table (filled in by hand, or kept from an earlier run)
    # comes first.
    if TABLE.get(e["Id"], (0, 0))[0] > 0:
        lo, hi = TABLE[e["Id"]]
        return (lo + hi) // 2
    buy = e.get("Buy") or 0
    sell = e.get("Sell") or buy // 2
    avg, seen = market(e["Id"], refresh)
    # Some items carry a placeholder NPC price of 20z; only a real one counts.
    if is_equip(e) and e["Id"] in NPC_SOLD and buy >= 100:
        # Players undercut the NPC a little rather than match it.
        return max(int(buy * 0.9), sell + 1)
    if avg is None or seen < 20:
        if e["Id"] in NPC_SOLD and (buy >= 100 or not is_equip(e)):
            return max(buy, sell + 1)
        return None
    if e.get("Type") == "Card":
        return avg if avg <= 30_000_000 else None
    if is_equip(e):
        # An average far above an item's NPC value is carded and refined
        # copies talking; a plain one sells near the NPC price.
        if buy >= 100 and avg > buy * 20:
            return max(int(buy * 0.9), sell + 1)
        if 40 <= buy < 100 and avg > buy * 500:
            return max(buy * 20, 1000)
        # Equipment "worth" a few zeny is a junk listing, not a price.
        return avg if 50 <= avg <= 15_000_000 else None
    # Consumables and loot: an average hundreds of times the NPC value is a
    # troll listing (Green Potion "99,990,000z") pulling the mean.
    ref = max(buy, sell * 2, 1)
    if avg > ref * 400 and avg > 50_000:
        return max(ref, sell + 1)
    return max(avg, sell + 1)


def tidy(p):
    if p >= 10000:
        return p // 500 * 500
    if p >= 1000:
        return p // 50 * 50
    if p >= 100:
        return p // 5 * 5
    return max(p, 1)


REFINE_ORE = {1: "Phracon", 2: "Emveretarcon", 3: "Oridecon", 4: "Oridecon", 0: "Elunium"}
# Success chance for each level past the safe limit; a failure destroys the item.
OVER_SAFE_ODDS = [0.6, 0.4, 0.4, 0.2, 0.2, 0.1]


def safe_limit(e):
    if e.get("Type") == "Weapon":
        return {1: 7, 2: 6, 3: 5, 4: 4}.get(e.get("WeaponLevel", 1), 4)
    return 4


def refine_steps(name):
    e = item(name)
    if not e:
        return []
    s = safe_limit(e)
    return [s, s + 1, s + 2, s + 3]


def refined_price(e, base, r, refresh):
    """What it cost to make, plus a little: ore up to the safe limit, then the
    expected cost of each further level, failures and lost items included."""
    ore = item(REFINE_ORE[e.get("WeaponLevel", 1) if e.get("Type") == "Weapon" else 0])
    ore_p = price(ore, refresh) or 1000
    s = safe_limit(e)
    cost = base + min(r, s) * ore_p
    for k in range(max(0, r - s)):
        cost = (cost + ore_p) / OVER_SAFE_ODDS[min(k, len(OVER_SAFE_ODDS) - 1)]
    return int(cost * 1.15)


def amount_for(e, p, rng):
    if is_equip(e) or e.get("Type") == "Card":
        return 1
    if p < 1_000:
        return rng.choice([50, 100, 150, 200, 300])
    if p < 20_000:
        return rng.choice([10, 20, 30, 50])
    if p < 200_000:
        return rng.choice([3, 5, 10])
    return rng.choice([1, 2, 3])

# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------
#
# key:    VendorKey suffix (prontera-vendors/<key>)
# job:    the shell's sprite; a job that can vend on a real server
# pick:   items per stall [min, max]; max_slots caps it (MC_VENDING 10 = 12 max)
# titles: shop signs; {name} is the stall owner's own name
# weight: share of the Vendors setting (Count in Spawns)
# one of:
#   items: hand list: "Aegis_Name", or dict(item=, refine=, element=, stars=, cards=, price=)
#   rule:  function(item_entry) -> bool over the whole item database
#   area:  spawn files in npc/re/mobs/dungeons whose monsters' drops it sells
#   boss:  True -> what bosses and MVPs drop that ordinary monsters don't

def weapon(e, *subtypes, lv=None):
    if e.get("Type") != "Weapon":
        return False
    if subtypes and e.get("SubType") not in subtypes:
        return False
    if lv and e.get("WeaponLevel", 1) not in lv:
        return False
    return True


def locs(e):
    return set((e.get("Locations") or {}).keys())


FORGE_BASE = {  # plain forged price, before stars
    "Knife": 12000, "Cutter": 15000, "Main_Gauche": 22000, "Dirk": 35000, "Dagger": 35000,
    "Stiletto": 70000, "Gladius": 110000, "Damascus": 160000,
    "Katar": 90000, "Jur": 120000, "Jamadhar": 160000,
}


def forged(name, element, stars=0):
    p = FORGE_BASE[name] * (1 + stars) * (4 if stars == 3 else 1)
    return dict(item=name, element=element, stars=stars, price=p)


ELEMENTS = ["Fire", "Water", "Earth", "Wind"]

THEMES = [
    dict(key="general_gear", job="Merchant", pick=[6, 10], weight=1,
         titles=["wts potz n stuff fs", "cheap gear, bargains", "fresh wares, come in", "stocked up, buy now",
                 "AFK vending <3", "wts random stuff fs", "junk n jewels", "clearing stash, buy", "{name}'s Shop"],
         items=["Red_Potion", "Orange_Potion", "Yellow_Potion", "White_Potion", "Blue_Potion", "Wing_Of_Fly",
                "Wing_Of_Butterfly", "Awakening_Potion", "Center_Potion", "Knife", "Sword", "Buckler", "Cotton_Shirt",
                "Sandals", "Hood", "Jellopy", "Fluff", "Clover", "Phracon", "Emveretarcon", "Elunium", "Oridecon"]),
    dict(key="forge_supplies", job="Whitesmith", pick=[5, 8], weight=1,
         titles=["ores n elu fs", "wts forging mats", "oridecon elunium cheap", "upgrade mats here",
                 "smith supplies fs", "stones n ores", "{name}'s Forge Goods"],
         items=["Phracon", "Emveretarcon", "Oridecon", "Elunium", "Steel", "Iron", "Iron_Ore", "Coal",
                "Flame_Heart", "Mistic_Frozen", "Rough_Wind", "Great_Nature", "Star_Crumb", "Oridecon_Stone",
                "Elunium_Stone", "Boody_Red", "Crystal_Blue", "Wind_Of_Verdure", "Yellow_Live"]),
    dict(key="potions", job="Alchemist", pick=[6, 10], weight=1,
         titles=["S> pots", "potion seller", "wts whites n blues", "pots cheaper than npc", "{name}'s Pharmacy",
                 "fresh pots"],
         items=["Red_Potion", "Orange_Potion", "Yellow_Potion", "White_Potion", "Blue_Potion", "Awakening_Potion",
                "Berserk_Potion", "Panacea", "Royal_Jelly", "Yggdrasilberry", "Seed_Of_Yggdrasil", "Center_Potion",
                "Grape", "Honey", "Strawberry", "Speed_Up_Potion", "Anodyne", "Aloebera", "Fruit_Of_Mastela",
                "Leaf_Of_Yggdrasil", "Box_Of_Thunder", "Wing_Of_Fly", "Wing_Of_Butterfly"]),
    dict(key="common_cards", job="HighMerchant", pick=[4, 8], weight=1,
         titles=["cards cheap", "S> cards", "common cards fs", "card shop", "{name}'s Card Binder", "cards cards cards"],
         rule=lambda e: e.get("Type") == "Card" and e["Id"] in COMMON_CARDS),
    dict(key="rare_cards", job="HighMerchant", pick=[2, 4], weight=1,
         titles=["rare cards", "S> good cards", "cards, no lowballs", "{name}'s Rare Cards"],
         rule=lambda e: e.get("Type") == "Card" and e["Id"] in RARE_CARDS),
    dict(key="headgear", job="Blacksmith", pick=[5, 9], weight=1,
         titles=["S> hats", "headgear sale", "hats n masks", "look good, buy hats", "{name}'s Hat Rack"],
         rule=lambda e: e.get("Type") == "Armor" and locs(e) & {"Head_Top", "Head_Mid", "Head_Low"}
         and not any(l.startswith("Costume") for l in locs(e)) and e.get("Slots", 0) == 0),
    dict(key="low_weapons", job="Blacksmith", pick=[6, 10], weight=1,
         titles=["weapons for newbies", "S> starter weapons", "cheap weapons", "lvl 1 weps fs"],
         rule=lambda e: weapon(e, lv={1}) and e["Id"] in NPC_SOLD),
    dict(key="mid_weapons", job="Whitesmith", pick=[5, 9], weight=1,
         titles=["S> weapons", "weapons shop", "lvl 2-3 weapons", "{name}'s Armory", "good weps fs"],
         rule=lambda e: weapon(e, lv={2, 3}) and e.get("Slots", 0) > 0),
    dict(key="elemental_daggers", job="Whitesmith", pick=[5, 9], weight=1,
         titles=["S> elemental daggers", "fire/ice/wind/earth daggers", "forged daggers fs", "{name}'s Forge",
                 "ele daggers, very strong too"],
         items=[forged(d, el, st) for d in ("Main_Gauche", "Dirk", "Stiletto", "Gladius", "Damascus")
                for el in ELEMENTS for st in (0,)] + [forged("Stiletto", el, 1) for el in ELEMENTS]
         + [forged("Gladius", el, 3) for el in ("Fire", "Water")]),
    dict(key="katars", job="Whitesmith", pick=[4, 8], weight=1,
         titles=["katars only", "S> katars", "sin weapons", "for assassins", "{name}'s Katars"],
         rule=lambda e: weapon(e, "Katar") and e.get("Slots", 0) > 0,
         extra=[forged(k, el) for k in ("Katar", "Jur", "Jamadhar") for el in ELEMENTS]),
    dict(key="costumes", job="Alchemist", pick=[3, 6], weight=1,
         titles=["costumes fs", "look cute", "S> costumes", "{name}'s Wardrobe", "fashion sale"],
         rule=lambda e: e.get("Type") == "Armor" and any(l.startswith("Costume") for l in locs(e))),
    dict(key="ice_pick", job="Whitesmith", pick=[1, 1], weight=1,
         titles=["S> Ice Pick", "S>Ice Pick", "Ice Pick here", "wts ice pick"],
         items=["House_Auger"]),
    dict(key="accessories", job="Merchant", pick=[4, 8], weight=1,
         titles=["accessories", "S> rings n stuff", "unslotted accs cheap", "{name}'s Jewelry"],
         rule=lambda e: e.get("Type") == "Armor" and locs(e) & {"Right_Accessory", "Left_Accessory", "Both_Accessory"}
         and e.get("Slots", 0) == 0),
    dict(key="converters", job="Alchemist", pick=[3, 6], weight=1,
         titles=["converters", "S> ele converters", "fire/water/wind/earth conv", "endow stuff fs"],
         items=["Elemental_Fire", "Elemental_Water", "Elemental_Earth", "Elemental_Wind", "Fire_Converter_Box",
                "Water_Converter_Box", "Wind_Converter_Box", "Earth_Converter_Box", "Boody_Red", "Crystal_Blue",
                "Wind_Of_Verdure", "Yellow_Live", "Holy_Water"]),
    dict(key="starter_gear", job="Merchant", pick=[6, 10], weight=1,
         titles=["newbie gear", "S> starter set", "for new players", "cheap noob gear", "{name}'s Starter Kits"],
         items=["Knife_", "Cutter_", "Main_Gauche_", "Sword_", "Falchion_", "Bow_", "Rod_", "Club_", "Cotton_Shirt_",
                "Adventurere's_Suit_", "Wooden_Mail_", "Guard_", "Buckler_", "Hood_", "Muffler_",
                "Sandals_", "Shoes_", "Bandana", "Cap", "Hat", "Red_Potion", "Wing_Of_Fly"]),
    dict(key="refined_weapons", job="Whitesmith", pick=[3, 6], weight=1,
         titles=["+7 weapons", "refined weapons", "S> high refine weps", "{name}'s Refinery", "+8 +9 weapons fs"],
         items=[dict(item=w, refine=r) for w in ("Knife_", "Main_Gauche_", "Stiletto", "Gladius", "Damascus", "Katar",
                                                  "Composite_Bow", "Mace", "Bastard_Sword", "Pike", "Rod_", "Jur")
                for r in refine_steps(w)]),
    dict(key="refined_armor", job="Whitesmith", pick=[3, 6], weight=1,
         titles=["refined armor", "+4 to +7 armor", "S> safe armor", "{name}'s Armory", "high refine armor fs"],
         items=[dict(item=a, refine=r) for a in ("Chain_Mail_", "Saint_Robe_", "Silk_Robe_", "Formal_Suit",
                                                  "Guard_", "Buckler_", "Manteau_", "Muffler_", "Boots_", "Shoes_", "Helm_")
                for r in (4, 5, 6, 7)]),
    dict(key="gemstones", job="Merchant", pick=[5, 9], weight=1,
         titles=["S> gems", "jewels n gemstones", "blue gems cheap", "{name}'s Jeweler", "diamonds fs"],
         items=["Blue_Gemstone", "Yellow_Gemstone", "Red_Gemstone", "Dark_Red_Jewel", "Violet_Jewel", "Skyblue_Jewel",
                "Azure_Jewel", "Scarlet_Jewel", "Cardinal_Jewel", "Blue_Jewel", "White_Jewel", "Golden_Jewel",
                "Bluish_Green_Jewel", "Crystal_Jewel", "Crystal_Jewel_", "Crystal_Jewel__", "Crystal_Jewel___"]),
    dict(key="healing", job="Alchemist", pick=[6, 10], weight=1,
         titles=["S> herbs n food", "healing items", "cheap heals", "{name}'s Kitchen", "food fs"],
         items=["Red_Herb", "Yellow_Herb", "White_Herb", "Blue_Herb", "Green_Herb", "Apple", "Banana", "Grape",
                "Carrot", "Meat", "Honey", "Royal_Jelly", "Strawberry", "Lemon", "Orange", "Cheese", "Popped_Rice",
                "Chocolate", "Bread", "Sweet_Potato_", "Yggdrasilberry", "Fruit_Of_Mastela"]),
    dict(key="undies", job="Merchant", pick=[2, 4], weight=1,
         titles=["undershirt + pantie", "S> undies", "Undershirt n Pantie fs", "{name}'s Laundry"],
         items=["Undershirt", "Undershirt_", "G_Strings", "G_Strings_", "Old_Pant", "Tiger_Skin_Panties"]),
    dict(key="supplies", job="Alchemist", pick=[6, 10], weight=1,
         titles=["gems n arrows", "S> blue gems", "skill supplies", "arrows cheap", "{name}'s Supplies"],
         items=["Blue_Gemstone", "Yellow_Gemstone", "Red_Gemstone", "Holy_Water", "Silver_Arrow", "Fire_Arrow",
                "Crystal_Arrow", "Arrow_Of_Wind", "Stone_Arrow", "Immatrial_Arrow", "Sleep_Arrow", "Oridecon_Arrow",
                "Acid_Bottle", "Fire_Bottle", "Empty_Bottle", "Medicine_Bowl", "Detrimindexta", "Karvodailnirol"]),
    dict(key="pets", job="Merchant", pick=[4, 8], weight=1,
         titles=["taming items", "S> pet stuff", "pet food n eggs", "{name}'s Pet Shop", "tame a poring"],
         items=["Pet_Food", "Unripe_Apple", "Orange_Juice", "Earthworm_The_Dude", "Rotten_Fish", "Bitter_Herb",
                "Monster_Juice", "Book_Of_Devil", "Fatty_Chubby_Earthworm", "Silver_Knife_Of_Chaste",
                "Monster_Oxygen_Mask", "Bark_Shorts", "Pet_Incubator", "Stuffed_Doll", "Green_Lace", "Sweet_Milk",
                "Shining_Stone", "Singing_Flower"]),
    dict(key="boss_loot", job="HighMerchant", pick=[3, 6], weight=1,
         titles=["boss loot", "mini boss drops", "rare drops", "{name}'s Trophies", "S> boss stuff"],
         boss=True),
]

THEMES += [
    dict(key="mvp_items", job="HighMerchant", pick=[2, 5], weight=1,
         titles=["MVP items", "S> mvp drops", "mvp loot fs", "{name}'s MVP Spoils", "rare mvp stuff"],
         mvp=True),
    dict(key="bloody_branches", job="Merchant", pick=[1, 2], weight=1,
         titles=["S> BB", "BBs cheap", "bloody branch fs", "BB / DB", "S>Bloody Branch"],
         items=["Bloody_Dead_Branch", "Branch_Of_Dead_Tree"]),
    dict(key="old_boxes", job="Merchant", pick=[1, 3], weight=1,
         titles=["S> OBB OPB", "OBB / OPB", "old boxes fs", "gamble boxes", "S>OPB"],
         items=["Old_Blue_Box", "Old_Violet_Box", "Old_Card_Album"]),
    dict(key="card_albums", job="HighMerchant", pick=[1, 2], weight=1,
         titles=["S> OCA MCA", "OCA / MCA", "card albums", "S>OCA", "try your luck: OCA"],
         items=["Old_Card_Album", "Magic_Card_Album"]),
    dict(key="crimson_weapons", job="Whitesmith", pick=[3, 6], weight=1,
         titles=["Crimson weapons", "S> crimson", "crimson katar/mace/dagger", "{name}'s Crimson Arsenal", "S> +7 crimson"],
         rule=lambda e: e.get("Type") == "Weapon" and e["Name"].startswith("Crimson ") and not e["AegisName"].endswith("_LT"),
         extra=[dict(item=w, refine=r) for w in ("Scarlet_Katar", "Scarlet_Mace", "Scarlet_Dagger", "Scarlet_Saber",
                                                  "Scarlet_Twohand_Sword") for r in (7, 9)]),
    dict(key="shadow_gear", job="Creator", pick=[3, 6], weight=1,
         titles=["shadow gear", "S> shadow equips", "shadows fs", "{name}'s Shadows"],
         rule=lambda e: e.get("Type") in ("ShadowGear", "Shadowgear")),
    dict(key="hunters_haul", job="Blacksmith", pick=[6, 10], weight=1,
         titles=["Stuff", "loot from today", "random drops", "cleaning my cart", "hunting haul", "{name}'s Leftovers"],
         rule=lambda e: e.get("Type") in ("Weapon", "Armor", "Card") and market(e["Id"], False)[1] >= 300),
    dict(key="ygg_ori_elu", job="Creator", pick=[3, 5], weight=1,
         titles=["YGG/ORI/ELU", "ygg ori elu", "S> yggs", "ori elu ygg fs"],
         items=["Yggdrasilberry", "Seed_Of_Yggdrasil", "Leaf_Of_Yggdrasil", "Oridecon", "Elunium",
                "Oridecon_Stone", "Elunium_Stone"]),
    dict(key="slim_potions", job="Creator", pick=[2, 3], weight=1,
         titles=["slims", "S> slim whites", "condensed pots", "{name}'s Slims", "slim potions cheap"],
         items=["Red_Slim_Potion", "Yellow_Slim_Potion", "White_Slim_Potion"]),
]

# Class shops: gear that a class (family) can wear and few others can,
# the kind of stall that reads "for Wizards" or "Knight gear".
# (key, titles, jobs that make it theirs)
def class_gear(jobs):
    def rule(e):
        if e.get("Type") not in ("Weapon", "Armor") or not tradeable(e):
            return False
        allowed = {k for k, v in (e.get("Jobs") or {}).items() if v}
        if not allowed or "All" in allowed or not allowed & jobs:
            return False
        return len(allowed - jobs) <= 3
    return rule


for _key, _titles, _jobs in [
    ("class_knight", ["Knight gear", "for knights", "S> spears n 2h swords", "peco knight stuff"], {"Knight", "Swordman"}),
    ("class_crusader", ["Crusader gear", "for crusaders", "S> shields n spears", "paladin stuff"], {"Crusader"}),
    ("class_wizard", ["Wizard gear", "for wizards", "S> staffs n robes", "mage stuff fs"], {"Wizard", "Mage"}),
    ("class_sage", ["Sage gear", "for sages", "S> books", "professor stuff"], {"Sage"}),
    ("class_hunter", ["Hunter gear", "for hunters", "S> bows", "archer stuff"], {"Hunter", "Archer"}),
    ("class_bard_dancer", ["Bard/Dancer gear", "S> instruments n whips", "for bards n dancers", "music shop"], {"BardDancer"}),
    ("class_priest", ["Priest gear", "for priests", "S> maces n rods", "acolyte stuff"], {"Priest", "Acolyte"}),
    ("class_monk", ["Monk gear", "for monks", "S> knuckles", "champ stuff"], {"Monk"}),
    ("class_assassin", ["Assassin gear", "for sins", "S> katars n daggers", "sinx stuff"], {"Assassin", "Thief"}),
    ("class_rogue", ["Rogue gear", "for rogues", "S> rogue stuff", "stalker stuff"], {"Rogue"}),
    ("class_blacksmith", ["Blacksmith gear", "for smiths", "S> axes", "WS stuff"], {"Blacksmith", "Merchant"}),
    ("class_alchemist", ["Alchemist gear", "for alchemists", "S> alche stuff", "creator stuff"], {"Alchemist"}),
    ("class_taekwon", ["Taekwon gear", "for TK / SG / SL", "star gladiator stuff", "soul linker gear"], {"Taekwon", "StarGladiator", "SoulLinker"}),
    ("class_ninja", ["Ninja gear", "for ninjas", "S> huuma n kunai", "kagerou/oboro stuff"], {"Ninja", "KagerouOboro"}),
    ("class_gunslinger", ["Gunslinger gear", "for gunslingers", "S> guns", "rebel stuff"], {"Gunslinger", "Rebellion"}),
    ("class_super_novice", ["Super Novice gear", "for SN", "S> SN stuff", "super novice only"], {"SuperNovice", "Novice"}),
    ("class_summoner", ["Doram gear", "for summoners", "S> doram stuff", "kitty gear"], {"Summoner", "Spirit_Handler"}),
]:
    THEMES.append(dict(key=_key, job=random.Random(_key).choice(["Merchant", "Blacksmith", "Whitesmith", "Alchemist", "Creator"]),
                       pick=[5, 9], weight=1, rule=class_gear(_jobs), titles=_titles + [f"{{name}}'s {_titles[0]}"]))

# Shops by weapon type and by armor slot, the way many players sort a cart.
def wtype(*subtypes):
    return lambda e: e.get("Type") == "Weapon" and e.get("SubType") in subtypes


def aslot(*slots):
    return lambda e: e.get("Type") == "Armor" and bool(locs(e) & set(slots)) and not any(
        l.startswith("Costume") for l in locs(e))


for _key, _titles, _rule in [
    ("type_daggers", ["daggers", "S> daggers", "knives n daggers"], wtype("Dagger")),
    ("type_swords", ["swords", "S> 1h swords", "blades fs"], wtype("1hSword")),
    ("type_twohanders", ["2h weapons", "S> two-handers", "big swords n axes"], wtype("2hSword", "2hAxe")),
    ("type_spears", ["spears", "S> spears n lances", "pointy things"], wtype("1hSpear", "2hSpear")),
    ("type_axes", ["axes", "S> axes", "axes for smiths"], wtype("1hAxe", "2hAxe")),
    ("type_maces", ["maces", "S> maces", "blunt weapons"], wtype("Mace")),
    ("type_staves", ["staves n rods", "S> staffs", "magic sticks"], wtype("Staff", "2hStaff")),
    ("type_bows", ["bows", "S> bows", "bows n crossbows"], wtype("Bow")),
    ("type_books", ["books", "S> books", "reading material"], wtype("Book")),
    ("type_knuckles", ["knuckles", "S> claws", "fists"], wtype("Knuckle")),
    ("type_music", ["instruments n whips", "S> whips", "music n dance"], wtype("Musical", "Whip")),
    ("type_guns", ["guns", "S> guns", "pew pew"], wtype("Revolver", "Rifle", "Gatling", "Shotgun", "Grenade")),
    ("type_huuma", ["huuma", "S> huuma shuriken", "ninja stars"], wtype("Huuma")),
    ("slot_garments", ["garments", "S> capes", "manteaus n mufflers"], aslot("Garment")),
    ("slot_footgear", ["shoes n boots", "S> footgear", "boots fs"], aslot("Shoes")),
    ("slot_shields", ["shields", "S> shields", "guards n bucklers"], aslot("Left_Hand")),
    ("slot_armor", ["armor", "S> body armor", "suits n robes"], aslot("Armor")),
    ("slotted_gear", ["slotted gear", "S> [1] slot stuff", "slotted equips"],
     lambda e: e.get("Type") == "Armor" and e.get("Slots", 0) > 0 and not any(l.startswith("Costume") for l in locs(e))),
    ("ammo", ["ammo", "S> arrows n bullets", "ammo cheap", "kunai n bullets"],
     lambda e: e.get("Type") == "Ammo"),
    ("scrolls", ["scrolls", "S> magic scrolls", "spell scrolls fs"],
     lambda e: e.get("Type") in ("Usable", "DelayConsume") and "Scroll" in e["Name"]),
    ("dyes", ["dyes", "S> dyestuffs", "colors n cloth"],
     lambda e: e.get("Type") == "Etc" and ("Dyestuff" in e["Name"] or "Dyestuffs" in e["Name"])),
    ("rare_etc", ["rare loot", "collector items", "S> rare etc"],
     lambda e: e.get("Type") == "Etc" and (market(e["Id"], False)[0] or 0) >= 100_000),
]:
    THEMES.append(dict(key=_key, job=random.Random(_key).choice(["Merchant", "Blacksmith", "Whitesmith", "Alchemist", "Creator"]),
                       pick=[5, 9], weight=1, rule=_rule, titles=_titles + [f"{{name}}'s {_titles[0].capitalize()}"]))

# Mostly random stalls: a broad pool each, sampled at random rather than by
# popularity, with mostly generic signs. Each reads like a different player
# emptying a different kind of cart.
for _key, _titles, _rule in [
    ("random_loot", ["junk n loot", "drops", "loot"], lambda e: e["Id"] in ANY_DROP and e.get("Type") == "Etc"),
    ("random_consumables", ["consumables", "useables", "stuff for hunting"],
     lambda e: e.get("Type") in ("Healing", "Usable", "DelayConsume")),
    ("random_equipment", ["equips", "gear", "old gear"],
     lambda e: e.get("Type") in ("Weapon", "Armor") and (market(e["Id"], False)[0] or 0) <= 2_000_000),
    ("random_cheap", ["Cart Clearance", "MEGA CLEARANCE", "everything cheap", "dirt cheap"],
     lambda e: e.get("Type") != "Card" and 0 < (market(e["Id"], False)[0] or 0) <= 5_000),
    ("random_mixed", ["random", "a bit of everything", "misc"],
     lambda e: e.get("Type") in ("Weapon", "Armor", "Card", "Etc", "Usable", "Healing") and market(e["Id"], False)[1] >= 100),
]:
    THEMES.append(dict(key=_key, job=random.Random(_key).choice(["Merchant", "Blacksmith", "Alchemist", "Creator"]),
                       pick=[6, 10], weight=1, rule=_rule, sample="random", limit=60, generic=6,
                       titles=_titles))

# Loot by monster level: drops of ordinary monsters in a level band that
# spawn somewhere. (key, title, low, high)
for _key, _title, _lo, _hi in [("loot_lv1_20", "lvl 1-20 mob loot", 1, 20), ("loot_lv21_40", "lvl 21-40 mob loot", 21, 40),
                               ("loot_lv41_60", "lvl 41-60 mob loot", 41, 60), ("loot_lv61_80", "lvl 61-80 mob loot", 61, 80),
                               ("loot_lv81_99", "lvl 81-99 mob loot", 81, 99)]:
    THEMES.append(dict(key=_key, job="Merchant", pick=[6, 10], weight=1, levels=(_lo, _hi),
                       titles=[_title, f"lv {_lo}-{_hi} drops", f"loot from {_lo}-{_hi} mobs", "mob loot cheap",
                               f"{{name}}'s Loot Bag"]))

# Generic shop signs. Real stalls often say nothing about what they sell;
# these are the kind sampled from iRO shops (no player names). Each theme
# gets a few, so about a third of signs are like this.
GENERIC_TITLES = ["Stuff", "SALE", "Happy hunting!", "...", "zzz", "Things.", "etc", "cheap stuff", "junk shop",
                  "Goodies", "This looks good", "AFK-----AFK", "Come on", "Come here u", "Sell", "See",
                  "Stuff you might want", "Bringing Simples You Need Cheap", "cheap stuff 2", "sale", "random"]

# Dungeon loot stalls: what the monsters of a place drop (no cards; those
# have their own stalls). (key, title, spawn files)
AREAS_LOOT = [
    ("byalan", "Byalan Drops", ["iz_dun.txt"]),
    ("geffenia", "Geffenia Drops", ["gefenia.txt"]),
    ("kiel", "Kiel Drops", ["kh_dun.txt"]),
    ("payon_cave", "Payon Cave Loot", ["pay_dun.txt"]),
    ("orc_dungeon", "Orc Dungeon Loot", ["orcsdun.txt"]),
    ("ant_hell", "Ant Hell Drops", ["anthell.txt"]),
    ("sphinx", "Sphinx Loot", ["in_sphinx.txt"]),
    ("pyramids", "Pyramid Loot", ["moc_pryd.txt"]),
    ("sunken_ship", "Sunken Ship Loot", ["treasure.txt"]),
    ("clock_tower", "Clock Tower Drops", ["c_tower.txt", "alde_dun.txt"]),
    ("glast_heim", "Glast Heim Loot", ["glastheim.txt"]),
    ("turtle_island", "Turtle Island Drops", ["tur_dun.txt"]),
    ("toy_factory", "Toy Factory Drops", ["xmas_dun.txt"]),
    ("niflheim", "Niflheim Loot", ["nif_dun.txt", "fields/niflheim.txt"]),
    ("magma", "Magma Dungeon Drops", ["mag_dun.txt"]),
    ("ice_cave", "Ice Cave Drops", ["ice_dun.txt"]),
    ("abyss_lake", "Abyss Lake Loot", ["abyss.txt"]),
    ("thanatos", "Thanatos Tower Loot", ["tha_t.txt"]),
    ("odin", "Odin Shrine Drops", ["odin.txt"]),
    ("juperos", "Juperos Loot", ["juperos.txt"]),
    ("bio_lab", "Bio Lab Loot", ["lhz_dun.txt"]),
    ("comodo_caves", "Comodo Cave Drops", ["beach_dun.txt"]),
    ("amatsu", "Amatsu Dungeon Drops", ["ama_dun.txt"]),
    ("sewers", "Culvert Drops", ["prt_sew.txt"]),
    ("guild_dungeon", "Guild Dungeon Loot", ["gld_dunSE.txt", "gld_re.txt"]),
]
for _key, _title, _files in AREAS_LOOT:
    _short = _title.split(" ")[0]
    THEMES.append(dict(key=_key, job=random.Random(_key).choice(["Merchant", "Blacksmith", "Alchemist", "Whitesmith", "Creator"]),
                       pick=[5, 9], weight=1, area=_files,
                       titles=[_title, f"S> {_short} loot", f"{_short.lower()} drops fs", f"fresh from {_short}",
                               f"{{name}}'s {_title}"]))

# Every item some monster drops, and how many kinds of monster drop it.
ANY_DROP = set()
DROPPERS = {}
for _m in MOBS.values():
    for _d in _m.get("Drops") or []:
        _e = item(_d["Item"])
        if _e:
            ANY_DROP.add(_e["Id"])
            DROPPERS[_e["Id"]] = DROPPERS.get(_e["Id"], 0) + 1
# A loot stall skips what more kinds of monster than this drop (Elunium,
# Yggdrasil Berry...), so each dungeon's stall shows its own loot.
LOOT_MAX_DROPPERS = 12

# Card tiers by the monster that drops them: level and boss class, since
# nearly every card drops at the same 0.01%.
COMMON_CARDS, RARE_CARDS = set(), set()
for _mid, _m in MOBS.items():
    if _mid in MVP_IDS:
        continue
    for _d in _m.get("Drops") or []:
        _e = item(_d["Item"])
        if not _e or _e.get("Type") != "Card" or _e["Id"] in MVP_CARDS:
            continue
        boss = (_m.get("Class") == "Boss")
        if _m.get("Level", 1) <= 60 and not boss:
            COMMON_CARDS.add(_e["Id"])
        else:
            RARE_CARDS.add(_e["Id"])
RARE_CARDS -= COMMON_CARDS

# ---------------------------------------------------------------------------
# Resolve
# ---------------------------------------------------------------------------

def area_items(files):
    seen = {}
    for mid, _ in spawns(files):
        if mid in MVP_IDS or mid not in MOBS:
            continue
        for d in MOBS[mid].get("Drops") or []:
            e = item(d["Item"])
            if e and e.get("Type") != "Card" and DROPPERS.get(e["Id"], 0) <= LOOT_MAX_DROPPERS:
                seen[e["Id"]] = e
    return list(seen.values())


def spawned_mobs():
    out = set()
    for root, _, files in os.walk(os.path.join(RA, "npc", "re", "mobs")):
        for f in files:
            for line in open(os.path.join(root, f), encoding="utf-8", errors="replace"):
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 4 and parts[1].startswith("monster"):
                    mid = mob_ref(parts[3])
                    if mid:
                        out.add(mid)
    return out


def level_items(lo, hi):
    spawned = spawned_mobs()
    out = {}
    for mid, m in MOBS.items():
        if mid in MVP_IDS or m.get("Class") == "Boss" or mid not in spawned or not lo <= m.get("Level", 1) <= hi:
            continue
        for d in m.get("Drops") or []:
            e = item(d["Item"])
            if e and e.get("Type") != "Card" and DROPPERS.get(e["Id"], 0) <= LOOT_MAX_DROPPERS:
                out[e["Id"]] = e
    return list(out.values())


def mvp_items():
    """What MVPs drop or reward, other than their cards."""
    out = {}
    for mid in MVP_IDS:
        m = MOBS[mid]
        for d in (m.get("Drops") or []) + (m.get("MvpDrops") or []):
            e = item(d["Item"])
            if e and e.get("Type") != "Card":
                out[e["Id"]] = e
    return list(out.values())


def boss_items():
    normal = set()
    for mid, m in MOBS.items():
        if mid not in MVP_IDS and m.get("Class") != "Boss":
            for d in m.get("Drops") or []:
                normal.add(d["Item"].lower())
    out = {}
    for mid, m in MOBS.items():
        if mid not in MVP_IDS and m.get("Class") == "Boss":
            for d in m.get("Drops") or []:
                e = item(d["Item"])
                if e and e.get("Type") != "Card" and d["Item"].lower() not in normal:
                    out[e["Id"]] = e
    return list(out.values())


def theme_candidates(theme):
    """The items a rule, area or loot theme considers. A rule can match
    thousands, so this is a bounded set: everything already priced, plus the
    lowest ids (the classic items a Prontera sidewalk would carry) up to
    CANDIDATE_CAP."""
    candidates = []
    if "rule" in theme:
        candidates = [e for e in ITEMS_BY_ID.values() if theme["rule"](e)]
    elif "area" in theme:
        candidates = area_items(theme["area"])
    elif theme.get("boss"):
        candidates = boss_items()
    elif theme.get("mvp"):
        candidates = mvp_items()
    elif "levels" in theme:
        candidates = level_items(*theme["levels"])
    candidates = [e for e in candidates if tradeable(e)]
    cached = [e for e in candidates if str(e["Id"]) in CACHE]
    rest = sorted((e for e in candidates if str(e["Id"]) not in CACHE), key=lambda e: e["Id"])
    return cached + rest[:max(0, CANDIDATE_CAP - len(cached))]


def prefetch(themes, workers=4, everything=False):
    """Fetch every price the themes will ask for (or, with everything, every
    tradeable item's), a few at a time."""
    from concurrent.futures import ThreadPoolExecutor
    want = {e["Id"] for e in ITEMS_BY_ID.values() if tradeable(e)} if everything else set()
    for t in themes:
        for spec in t.get("items", []) + t.get("extra", []):
            e = item(spec["item"] if isinstance(spec, dict) else spec)
            if e:
                want.add(e["Id"])
        want.update(e["Id"] for e in theme_candidates(t))
    want.update(item(n)["Id"] for n in REFINE_ORE.values())
    missing = sorted(i for i in want if str(i) not in CACHE)
    print(f"  fetching {len(missing)} prices ({len(want)} wanted)", file=sys.stderr)
    done = 0
    with ThreadPoolExecutor(workers) as pool:
        for iid, res in zip(missing, pool.map(lambda i: (time.sleep(0.2), fetch(i))[1], missing)):
            CACHE[str(iid)] = res
            done += 1
            if done % 50 == 0:
                json.dump(CACHE, open(PRICES, "w"), indent=0, sort_keys=True)
                print(f"    {done}/{len(missing)}", file=sys.stderr)
    json.dump(CACHE, open(PRICES, "w"), indent=0, sort_keys=True)


def resolve(theme, refresh, rng):
    lines = []
    if "items" in theme or "extra" in theme:
        for spec in theme.get("items", []) + theme.get("extra", []):
            spec = spec if isinstance(spec, dict) else dict(item=spec)
            e = item(spec["item"])
            if not e:
                print(f"  {theme['key']}: no item {spec['item']}", file=sys.stderr)
                continue
            if not tradeable(e):
                continue
            p = spec.get("price")
            if p is None:
                p = price(e, refresh)
                if p is None:
                    # Hand-picked, so trust the market even above the caps
                    # (an Ice Pick really does go for tens of millions).
                    avg, seen = market(e["Id"], False)
                    p = avg if avg and seen >= 20 else None
                if p is None:
                    continue
                if spec.get("refine"):
                    p = refined_price(e, p, spec["refine"], refresh)
            lines.append((e, spec, p))
    candidates = theme_candidates(theme)
    if candidates:
        priced = []
        for e in candidates:
            if not tradeable(e):
                continue
            p = price(e, refresh)
            if p is None:
                continue
            priced.append((market(e["Id"], False)[1], e, p))
        limit = theme.get("limit", 30)
        if theme.get("sample") == "random":
            random.Random(theme["key"]).shuffle(priced)
        else:
            # The ones players actually trade most, so a stall reads familiar.
            priced.sort(key=lambda t: -t[0])
        for _, e, p in priced[:limit]:
            lines.append((e, dict(item=e["AegisName"]), p))
    return lines


def flow(d):
    parts = []
    for k, v in d.items():
        if isinstance(v, list):
            v = "[" + ", ".join(str(x) for x in v) + "]"
        parts.append(f"{k}: {v}")
    return "{ " + ", ".join(parts) + " }"


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def read_table():
    import csv
    out = {}
    if not os.path.exists(TABLE_CSV):
        return out
    # Excel may save it in the local code page; only Id and the numbers matter.
    with open(TABLE_CSV, encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        rows = csv.reader((l for l in f if not l.lstrip().startswith("#")),
                          delimiter=";" if sample.count(";") > sample.count(",") else ",")
        for row in rows:
            if not row or row[0].strip().lower() == "id" or len(row) < 3:
                continue
            try:
                iid = int(row[0]) if row[0].strip() else item(row[1].strip())["Id"]
                lo = int(row[2])
                hi = int(row[3]) if len(row) > 3 and row[3].strip() else lo
            except (ValueError, TypeError):
                continue
            out[iid] = (lo, max(lo, hi)) if lo > 0 else (0, 0)
    return out


def write_table():
    import csv
    os.makedirs(os.path.dirname(TABLE_CSV), exist_ok=True)
    # Every tradeable item gets a row: a price if the market had one, else 0,0
    # ("not priced yet") so it is there to fill in.
    for e in ITEMS_BY_ID.values():
        # Priced rows are kept as they are; 0,0 rows are tried again.
        if TABLE.get(e["Id"], (0, 0))[0] > 0 or not tradeable(e) or not e.get("Name"):
            continue
        p = price(e, False)
        if p is None:
            TABLE[e["Id"]] = (0, 0)
        else:
            band = 0.08 if p >= 1000 else 0.15
            TABLE[e["Id"]] = (tidy(max(1, int(p * (1 - band)))), tidy(int(p * (1 + band)) + 1))
    with open(TABLE_CSV, "w", encoding="utf-8", newline="") as f:
        f.write("# prontera-vendors price table: what each item sells for, as a range each\n"
                "# stall rolls inside. Edit freely; the server reads it at startup, and\n"
                "# tools/build_vendors.py keeps existing rows. Id decides, Name is for you.\n"
                "# 0,0 = no price yet: fill one in and re-run the generator, and the item\n"
                "# can then show up in the themes it fits.\n"
                "# Refined, forged and carded lines are priced in population_vendors.yml.\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Id", "Name", "Min", "Max"])
        for iid, (lo, hi) in sorted(TABLE.items(), key=lambda kv: (ITEMS_BY_ID[kv[0]]["Name"].lower(), kv[0])):
            w.writerow([iid, ITEMS_BY_ID[iid]["Name"], lo, hi])


TABLE = {}


def main():
    # --reprice starts the table over from market data (hand edits are lost).
    if "--reprice" not in sys.argv:
        TABLE.update(read_table())
    if "--all-prices" in sys.argv:
        prefetch(THEMES, everything=True)
    elif "--refresh-prices" in sys.argv:
        prefetch(THEMES)
    refresh = False
    rng = random.Random(1)
    vendors, profiles = [], []
    for t in THEMES:
        lines = resolve(t, refresh, rng)
        if not lines:
            print(f"  {t['key']}: nothing to sell, skipped", file=sys.stderr)
            continue
        key = PREFIX + t["key"]
        out = [f"  - VendorKey: {key}", "    Type: Pool", f"    Title: {q(t['titles'][0])}", "    TitleFromPool:"]
        titles = list(t["titles"]) + random.Random(t["key"]).sample(GENERIC_TITLES, t.get("generic", 3))
        out += [f"      - {q(x)}" for x in titles]
        lo, hi = t["pick"]
        max_slots = min(12, max(hi, 1))
        out += [f"    PickCount: [{lo}, {hi}]", f"    MaxSlots: {max_slots}",
                "    RotationHours: 4", "    RotationJitterMinutes: 30",
                "    PriceMistakeOneIn: 5000",
                "    Undercut: { Chance: 50, StepPct: [1, 5] }",
                "    Callouts: { EverySeconds: [90, 270], MapGapSeconds: 6 }",
                "    Pool:"]
        for e, spec, p in lines:
            d = {"Item": e["AegisName"], "Amount": amount_for(e, p, rng)}
            plain = not (spec.get("refine") or spec.get("element") or spec.get("stars"))
            if plain and TABLE.get(e["Id"], (0, 0))[0] > 0:
                d["Price"] = list(TABLE[e["Id"]])
            else:
                band = 0.08 if p >= 1000 else 0.15
                d["Price"] = [tidy(max(1, int(p * (1 - band)))), tidy(int(p * (1 + band)) + 1)]
                if plain:
                    TABLE[e["Id"]] = tuple(d["Price"])
            if spec.get("refine"):
                d["Refine"] = spec["refine"]
            if spec.get("element"):
                d["Element"] = spec["element"]
            if spec.get("stars"):
                d["Stars"] = spec["stars"]
            out.append(f"      - {flow(d)}")
        out += ["    Spawns:", "      - Map: prontera", f"        Count: {t['weight']}", "        Areas:"]
        out += [f"          - {flow(a)}" for a in AREAS]
        vendors.append("\n".join(out))
        profiles.append("\n".join([
            f"  - Profile: {key}_vendor",
            "    PlacementBound: true",
            "    Jobs:",
            f"      {t['job']}: para_merchant",
            "    NameProfile: default",
            "    Hair: [0, 42]",
            "    HairColor: [0, 131]",
            "    ClothesColor: [0, 699]",
            "    Flags:",
            "      - mortal",
            "    TownBehavior: vendor",
            f"    VendorKey: {key}",
            "    Script: |",
            "      setcart;",
        ]))
        print(f"  {t['key']}: {len(lines)} items", file=sys.stderr)
    write_table()

    head = (
        "###########################################################################\n"
        "# prontera-vendors — {what}\n"
        "# GENERATED by tools/build_vendors.py from rAthena's item, monster and\n"
        "# spawn databases and iRO market prices. Edit by hand if you like, but a\n"
        "# re-run overwrites this file; lasting changes belong in the script.\n"
        "###########################################################################\n"
    )
    vend_doc = head.format(what="vendor definitions") + (
        "#\n"
        "# One Pool vendor per theme. Each stall draws PickCount items from its Pool\n"
        "# with prices rolled inside each item's [min, max] (sometimes just under the\n"
        "# cheapest rival stall, never below the NPC sell price), and on a rare\n"
        "# 1-in-5000 per item lists one with a digit missing.\n"
        "#\n"
        "# Every theme spawns on both Prontera sidewalks. Count is the theme's share\n"
        "# of the mod's \"Vendors\" setting, which the mod's script hands to the\n"
        "# engine; rotation and callouts come from the settings too, and the values\n"
        "# here are what applies without them.\n"
        "###########################################################################\n\n"
        "Header:\n  Type: POPULATION_VENDORS_DB\n  Version: 1\n\nBody:\n"
    )
    pop_doc = head.format(what="vendor shell profiles") + (
        "#\n"
        "# One PlacementBound profile per theme: the engine finds it by VendorKey, not\n"
        "# by job, so the job is only the sprite (a job that can vend on a real\n"
        "# server) and it never displaces the engine's own vendors.\n"
        "###########################################################################\n\n"
        "Header:\n  Type: POPULATION_ENGINE_DB\n  Version: 2\n\nBody:\n"
    )
    open(os.path.join(MOD, "db", "population_vendors.yml"), "w", encoding="utf-8", newline="\n").write(
        vend_doc + "\n\n".join(vendors) + "\n")
    open(os.path.join(MOD, "db", "population_vendor_pop.yml"), "w", encoding="utf-8", newline="\n").write(
        pop_doc + "\n\n".join(profiles) + "\n")


if __name__ == "__main__":
    main()
