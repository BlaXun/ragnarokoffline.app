-- What the client calls item 30051 and the art it draws. Added to the
-- client's customItemInfo ahead of the base table (see docs/MODDING.md,
-- System/), so a table holding only this one item is all it needs -- the
-- client registers every entry in `tbl` itself. Saved as UTF-8.
--
-- identifiedResourceName is the ART, written in Korean the way the client
-- names it. 돋보기 is the Magnifier's icon and sprite, borrowed here so the
-- item needs no art of its own. Swap it for another item's Korean resource
-- name, or ship your own bitmap and sprite, to change the look; a name
-- that matches no file shows an apple icon and is logged in
-- state/assets/logs/missing-files.log.
tbl = {
	[30051] = {
		unidentifiedDisplayName = "Exp Card",
		unidentifiedResourceName = "돋보기",
		unidentifiedDescriptionName = {
			"A slip of paper that hums with a faint promise."
		},
		identifiedDisplayName = "Exp Card",
		identifiedResourceName = "돋보기",
		identifiedDescriptionName = {
			"Use it to gain a portion of the experience you need",
			"for your next level (both ^0000FFbase^000000 and ^0000FFjob^000000).",
			"^ffffff_^000000",
			"Drops on a small chance from any monster you kill.",
			"Bound to you briefly on drop; nobody else can pick it up first.",
			"^ffffff_^000000",
			"Weight: ^777777 1 ^000000"
		},
		slotCount = 0,
		ClassNum = 0
	}
}
