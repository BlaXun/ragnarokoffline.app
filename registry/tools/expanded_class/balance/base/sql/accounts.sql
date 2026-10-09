-- rig accounts: gmtest (group 99, all GM commands) and player (group 0)
INSERT INTO `login` (`userid`, `user_pass`, `sex`, `email`, `group_id`)
	SELECT 'gmtest', 'gmtest123', 'M', 'gm@rig.local', 99 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM `login` WHERE `userid` = 'gmtest');
INSERT INTO `login` (`userid`, `user_pass`, `sex`, `email`, `group_id`)
	SELECT 'player', 'player123', 'M', 'player@rig.local', 0 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM `login` WHERE `userid` = 'player');
INSERT INTO `login` (`userid`, `user_pass`, `sex`, `email`, `group_id`)
	SELECT 'fem', 'fem123', 'F', 'fem@rig.local', 0 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM `login` WHERE `userid` = 'fem');
INSERT INTO `login` (`userid`, `user_pass`, `sex`, `email`, `group_id`)
	SELECT 'axe', 'axe123', 'M', 'axe@rig.local', 0 FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM `login` WHERE `userid` = 'axe');
