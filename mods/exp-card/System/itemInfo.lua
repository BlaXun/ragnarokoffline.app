-- What the client calls items 30051..30070 and the art it draws. Added to
-- the client's customItemInfo ahead of the base table (see docs/MODDING.md,
-- System/), so a table holding these twenty entries is all it needs -- the
-- client registers every entry in `tbl` itself. Saved as UTF-8.
--
-- The two card families share their shape (weight, resource, description
-- layout), so this is a small loop over levels 1..10 instead of twenty
-- copy-pasted blocks -- keeps the exp values in the description in sync
-- with the +N text and the item_db numbers automatically.
--
-- identifiedResourceName is the ART, written in Korean the way the client
-- names it. 돋보기 is the Magnifier's icon and sprite, borrowed here so
-- the item needs no art of its own. Swap it for another item's Korean
-- resource name, or ship your own bitmap and sprite, to change the look;
-- a name that matches no file shows an apple icon and is logged in
-- state/assets/logs/missing-files.log.
tbl = {}

local EXP_PER_LEVEL = 6000    -- must match db/item_db.yml (level * EXP_PER_LEVEL)
local RESOURCE = "돋보기"

for level = 1, 10 do
	local exp = EXP_PER_LEVEL * level
	local baseName = "Base Exp Card Lv" .. level
	local jobName  = "Job Exp Card Lv"  .. level
	local baseDesc = {
		"^0000FF+" .. exp .. "^000000 base experience.",
		"^ffffff_^000000",
		"Drops on a small chance from any monster you kill.",
		"Bound to you briefly on drop; nobody else can pick it up first.",
		"Higher-level monsters drop higher-level cards.",
		"^ffffff_^000000",
		"Weight: ^777777 1 ^000000"
	}
	local jobDesc = {
		"^0000FF+" .. exp .. "^000000 job experience.",
		"^ffffff_^000000",
		"Drops on a small chance from any monster you kill.",
		"Bound to you briefly on drop; nobody else can pick it up first.",
		"Higher-level monsters drop higher-level cards.",
		"^ffffff_^000000",
		"Weight: ^777777 1 ^000000"
	}
	tbl[30050 + level] = {
		unidentifiedDisplayName = baseName,
		unidentifiedResourceName = RESOURCE,
		unidentifiedDescriptionName = baseDesc,
		identifiedDisplayName = baseName,
		identifiedResourceName = RESOURCE,
		identifiedDescriptionName = baseDesc,
		slotCount = 0,
		ClassNum = 0
	}
	tbl[30060 + level] = {
		unidentifiedDisplayName = jobName,
		unidentifiedResourceName = RESOURCE,
		unidentifiedDescriptionName = jobDesc,
		identifiedDisplayName = jobName,
		identifiedResourceName = RESOURCE,
		identifiedDescriptionName = jobDesc,
		slotCount = 0,
		ClassNum = 0
	}
end
